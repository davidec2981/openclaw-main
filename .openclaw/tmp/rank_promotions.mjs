import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import path from 'node:path';

const DAY_MS = 86400 * 1000;
const now = new Date("2026-07-03T12:02:00Z");
const nowMs = now.getTime();
const nowIso = now.toISOString();
const todayStr = nowIso.slice(0, 10);

// Params from cron job
const MIN_SCORE = 0.800;
const MIN_RECALL_COUNT = 3;
const MIN_UNIQUE_QUERIES = 3;
const RECENCY_HALF_LIFE_DAYS = 14;
const MAX_AGE_DAYS = 30;
const LIMIT = 10;

// Default weights from source code
const DEFAULT_WEIGHTS = {
    frequency: 0.24,
    relevance: 0.30,
    diversity: 0.15,
    recency: 0.15,
    consolidation: 0.10,
    conceptual: 0.06
};

const PROMOTION_MARKER_PREFIX = "openclaw-memory-promotion:";
const PROMOTION_SECTION_HEADING_RE = /^## Promoted From Short-Term Memory \(([^)]+)\)\s*$/;
const DEFAULT_MEMORY_FILE_MAX_CHARS = 10000;
const WRITE_OVERHEAD_RESERVE = 21;

function clamp(v) { return Math.max(0, Math.min(1, v)); }

function calcRecency(ageDays, halfLifeDays) {
    if (ageDays < 0) return 1;
    if (halfLifeDays <= 0) return 1;
    return Math.exp(-Math.LN2 / halfLifeDays * ageDays);
}

function calcConsolidation(recallDays) {
    if (!recallDays || recallDays.length === 0) return 0;
    if (recallDays.length === 1) return 0.2;
    const parsed = recallDays.map(d => Date.parse(d + "T00:00:00.000Z")).filter(Number.isFinite).sort((a,b) => a-b);
    if (parsed.length <= 1) return 0.2;
    const spanDays = Math.max(0, (parsed.at(-1) - parsed[0]) / DAY_MS);
    const spacing = clamp(Math.log1p(parsed.length - 1) / Math.log1p(4));
    const span = clamp(spanDays / 7);
    return clamp(0.55 * spacing + 0.45 * span);
}

function calcConceptual(conceptTags) {
    return clamp((conceptTags?.length || 0) / 6);
}

function normalizeSnippet(raw) {
    return (raw || "").trim().replace(/\s+/g, " ");
}

function formatPromotedSnippet(snippet, maxTokens = 160) {
    const limit = maxTokens * 4;
    const snip = normalizeSnippet(snippet || "(no snippet)").replace(/^[-*+]\s+/, "").trim() || "(no snippet)";
    if (snip.length <= limit) return snip;
    const hard = snip.slice(0, limit);
    const sentEnd = Math.max(hard.lastIndexOf(". "), hard.lastIndexOf("! "), hard.lastIndexOf("? "));
    const wordEnd = hard.lastIndexOf(" ");
    const cutAt = sentEnd >= Math.floor(limit * 0.55) ? sentEnd + 1 : wordEnd >= Math.floor(limit * 0.65) ? wordEnd : limit;
    return hard.slice(0, cutAt).trimEnd() + "...";
}

function extractPromotionMarkers(memoryText) {
    const markers = new Set();
    const matches = memoryText.matchAll(/<!--\s*openclaw-memory-promotion:([^\n]*?)\s*-->/gi);
    for (const match of matches) markers.add(match[1]?.trim());
    return markers;
}

function parseMemoryBlocks(content) {
    if (!content || content.length === 0) return [];
    const lines = content.split(/\r?\n/);
    const blocks = [];
    let currentLines = [];
    let currentKind = "preserved";
    let currentDate = null;

    const flush = () => {
        if (currentLines.length === 0) return;
        const text = currentLines.join("\n");
        if (currentKind === "promotion" && currentDate) {
            blocks.push({ kind: "promotion", date: currentDate, text });
        } else {
            blocks.push({ kind: "preserved", text });
        }
        currentLines = [];
        currentKind = "preserved";
        currentDate = null;
    };

    for (const line of lines) {
        if (line.startsWith("## ")) {
            flush();
            const match = PROMOTION_SECTION_HEADING_RE.exec(line);
            if (match) {
                currentKind = "promotion";
                currentDate = match[1];
            }
            currentLines = [line];
        } else {
            currentLines.push(line);
        }
    }
    flush();
    return blocks;
}

function joinBlocks(blocks) {
    return blocks.map(b => b.text).join("\n");
}

function compactMemory(existingMemory, newSection, budgetChars) {
    if (budgetChars <= 0) return { compacted: existingMemory, droppedDates: [] };
    const effectiveBudget = Math.max(0, budgetChars - WRITE_OVERHEAD_RESERVE);
    if (existingMemory.length + newSection.length <= effectiveBudget) {
        return { compacted: existingMemory, droppedDates: [] };
    }

    const blocks = parseMemoryBlocks(existingMemory);
    const promotionEntries = blocks
        .map((block, idx) => block.kind === "promotion" ? { index: idx, date: block.date, length: block.text.length } : null)
        .filter(Boolean)
        .sort((a, b) => a.date.localeCompare(b.date));

    if (promotionEntries.length === 0) return { compacted: existingMemory, droppedDates: [] };

    const droppedIndices = new Set();
    const droppedDates = [];
    let projectedSize = existingMemory.length;
    const separatorCost = blocks.length > 1 ? 1 : 0;

    for (const entry of promotionEntries) {
        if (projectedSize + newSection.length <= effectiveBudget) break;
        droppedIndices.add(entry.index);
        droppedDates.push(entry.date);
        projectedSize = Math.max(0, projectedSize - entry.length - separatorCost);
    }

    if (droppedIndices.size === 0) return { compacted: existingMemory, droppedDates: [] };
    return {
        compacted: joinBlocks(blocks.filter((_, i) => !droppedIndices.has(i))),
        droppedDates
    };
}

function buildPromotionSection(candidates, dayStr) {
    const heading = `## Promoted From Short-Term Memory (${dayStr})`;
    const lines = [heading, ""];
    for (const c of candidates) {
        const metadata = `[score=${c.score.toFixed(3)} recalls=${c.signalCount} avg=${c.avgScore.toFixed(3)} source=memory]`;
        lines.push(`<!-- ${PROMOTION_MARKER_PREFIX}${c.key} -->`);
        lines.push(`- ${formatPromotedSnippet(c.snippet)} ${metadata}`);
    }
    lines.push("");
    return lines.join("\n");
}

function rankWorkspace(workspaceDir) {
    const recallPath = path.join(workspaceDir, "memory", ".dreams", "short-term-recall.json");
    if (!existsSync(recallPath)) return null;

    let data;
    try { data = JSON.parse(readFileSync(recallPath, 'utf-8')); }
    catch { return { ws: workspaceDir, error: "parse-error", candidates: [], total: 0 }; }

    const entries = data.entries || {};
    const candidates = [];

    for (const [key, entry] of Object.entries(entries)) {
        if (entry.promotedAt) continue;
        if (entry.source !== "memory") continue;

        const recallCount = Math.max(0, Math.floor(entry.recallCount || 0));
        const dailyCount = Math.max(0, Math.floor(entry.dailyCount || 0));
        const groundedCount = Math.max(0, Math.floor(entry.groundedCount || 0));
        const signalCount = recallCount + dailyCount + groundedCount;
        if (signalCount < MIN_RECALL_COUNT) continue;

        const totalScore = Math.max(0, Number(entry.totalScore || 0));
        const avgScore = clamp(totalScore / Math.max(1, signalCount));

        const uniqueQueries = (entry.queryHashes || []).length;
        const contextDiversity = Math.max(uniqueQueries, (entry.recallDays || []).length);
        if (contextDiversity < MIN_UNIQUE_QUERIES) continue;

        const lastRecalledAt = entry.lastRecalledAt;
        let lastRecalledMs = Number.NEGATIVE_INFINITY;
        if (lastRecalledAt) {
            const parsed = Date.parse(lastRecalledAt);
            if (Number.isFinite(parsed)) lastRecalledMs = parsed;
        }
        const ageDays = Number.isFinite(lastRecalledMs) ? Math.max(0, (nowMs - lastRecalledMs) / DAY_MS) : 0;
        if (MAX_AGE_DAYS >= 0 && ageDays > MAX_AGE_DAYS) continue;

        const frequency = clamp(Math.log1p(signalCount) / Math.log1p(10));
        const relevance = avgScore;
        const diversity = clamp(contextDiversity / 5);
        const recency = clamp(calcRecency(ageDays, RECENCY_HALF_LIFE_DAYS));
        const consolidation = Math.max(calcConsolidation(entry.recallDays || []), clamp(groundedCount / 3));
        const conceptual = calcConceptual(entry.conceptTags || []);

        const score = DEFAULT_WEIGHTS.frequency * frequency +
                     DEFAULT_WEIGHTS.relevance * relevance +
                     DEFAULT_WEIGHTS.diversity * diversity +
                     DEFAULT_WEIGHTS.recency * recency +
                     DEFAULT_WEIGHTS.consolidation * consolidation +
                     DEFAULT_WEIGHTS.conceptual * conceptual;

        const clampedScore = clamp(score);
        if (clampedScore < MIN_SCORE) continue;

        candidates.push({
            key,
            path: entry.path,
            startLine: entry.startLine,
            endLine: entry.endLine,
            snippet: entry.snippet || "",
            signalCount,
            avgScore,
            maxScore: clamp(entry.maxScore || 0),
            uniqueQueries,
            ageDays,
            score: clampedScore,
            recallDays: entry.recallDays || [],
            conceptTags: entry.conceptTags || [],
            firstRecalledAt: entry.firstRecalledAt,
            lastRecalledAt: entry.lastRecalledAt
        });
    }

    candidates.sort((a, b) => b.score - a.score || b.signalCount - a.signalCount);
    return { ws: workspaceDir, candidates: candidates.slice(0, LIMIT), total: Object.keys(entries).length };
}

function promoteWorkspace(workspaceDir, dryRun = true) {
    const result = rankWorkspace(workspaceDir);
    if (!result || result.candidates.length === 0) return result;

    const memoryPath = path.join(workspaceDir, "MEMORY.md");
    let existingMemory = "";
    try { existingMemory = readFileSync(memoryPath, 'utf-8'); }
    catch { /* file doesn't exist yet */ }

    const existingMarkers = extractPromotionMarkers(existingMemory);
    const toAppend = result.candidates.filter(c => !existingMarkers.has(c.key));

    if (toAppend.length === 0) {
        result.action = "all-already-promoted";
        return result;
    }

    if (dryRun) {
        result.action = "would-promote";
        result.wouldAppend = toAppend.length;
        result.alreadyPromoted = result.candidates.length - toAppend.length;
        // Also read actual source snippets if possible
        for (const c of toAppend) {
            const srcPath = path.join(workspaceDir, c.path);
            if (existsSync(srcPath)) {
                try {
                    const srcLines = readFileSync(srcPath, 'utf-8').split(/\r?\n/);
                    const si = Math.max(0, c.startLine - 1);
                    const ei = Math.min(srcLines.length, c.endLine);
                    const actualSnippet = srcLines.slice(si, ei).join(" ").replace(/\s+/g, " ").trim();
                    if (actualSnippet && actualSnippet.length > 10) {
                        c.snippet = actualSnippet;
                    }
                } catch {}
            }
        }
        return result;
    }

    // Actually apply
    const section = buildPromotionSection(toAppend, todayStr);
    const compaction = compactMemory(existingMemory, section, DEFAULT_MEMORY_FILE_MAX_CHARS);
    const baseMemory = compaction.compacted;
    const header = baseMemory.trim().length > 0 ? "" : "# Long-Term Memory\n\n";

    const finalContent = header + (baseMemory ? (baseMemory.endsWith("\n") ? baseMemory : baseMemory + "\n") : "") + section;
    writeFileSync(memoryPath, finalContent, 'utf-8');

    // Mark entries as promoted in the store
    const recallPath = path.join(workspaceDir, "memory", ".dreams", "short-term-recall.json");
    try {
        let data = JSON.parse(readFileSync(recallPath, 'utf-8'));
        data.updatedAt = nowIso;
        for (const c of result.candidates) {
            if (data.entries[c.key]) {
                data.entries[c.key].promotedAt = nowIso;
            }
        }
        writeFileSync(recallPath, JSON.stringify(data, null, 2), 'utf-8');
    } catch {}

    result.action = "promoted";
    result.appended = toAppend.length;
    result.alreadyPromoted = result.candidates.length - toAppend.length;
    result.compactedDates = compaction.droppedDates;
    return result;
}

// MAIN
const workspaces = [
    "/root/.openclaw/workspace",
    "/root/.openclaw/workspace-trading",
    "/root/.openclaw/workspace-farmer",
    "/root/.openclaw/workspace-polyclaw",
    "/root/.openclaw/workspace-aihf",
    "/root/.openclaw/workspace-airdrop",
];

let totalPromoted = 0;
let totalAlready = 0;
let totalCandidates = 0;

console.log(`=== Memory Dreaming Promotion Run ===`);
console.log(`Time: ${nowIso}`);
console.log(`Criteria: minScore=${MIN_SCORE}, minRecalls=${MIN_RECALL_COUNT}, minUniqueQueries=${MIN_UNIQUE_QUERIES}, recencyHalfLife=${RECENCY_HALF_LIFE_DAYS}d, maxAge=${MAX_AGE_DAYS}d, limit=${LIMIT}`);
console.log();

for (const ws of workspaces) {
    const result = rankWorkspace(ws);
    const name = path.basename(ws);
    if (!result) {
        console.log(`${name}: no short-term recall file`);
        continue;
    }
    if (result.error) {
        console.log(`${name}: error=${result.error}`);
        continue;
    }

    console.log(`${name}: total=${result.total}, candidates=${result.candidates.length}`);
    totalCandidates += result.candidates.length;

    if (result.candidates.length > 0) {
        // Do actual promotion (not dry run)
        const promoteResult = promoteWorkspace(ws, false);
        if (promoteResult.action === "promoted") {
            console.log(`  → Promoted ${promoteResult.appended} new entries (${promoteResult.alreadyPromoted} already existed)`);
            totalPromoted += promoteResult.appended;
            totalAlready += promoteResult.alreadyPromoted;
            if (promoteResult.compactedDates?.length > 0) {
                console.log(`  → Compacted ${promoteResult.compactedDates.length} old promotion sections`);
            }
        }
        for (const c of result.candidates.slice(0, 3)) {
            const srcPath = path.join(ws, c.path);
            let fullSnippet = c.snippet;
            if (existsSync(srcPath)) {
                try {
                    const srcLines = readFileSync(srcPath, 'utf-8').split(/\r?\n/);
                    const si = Math.max(0, c.startLine - 1);
                    const ei = Math.min(srcLines.length, c.endLine);
                    fullSnippet = srcLines.slice(si, ei).join(" ").replace(/\s+/g, " ").trim() || c.snippet;
                } catch {}
            }
            console.log(`  - score=${c.score.toFixed(4)} sig=${c.signalCount} div=${c.uniqueQueries} age=${c.ageDays.toFixed(1)}d | ${fullSnippet.substring(0, 100)}`);
        }
    }
}

console.log();
console.log(`Summary: ${totalCandidates} total candidates across all workspaces`);
console.log(`Promoted: ${totalPromoted}, Already existing: ${totalAlready}`);
