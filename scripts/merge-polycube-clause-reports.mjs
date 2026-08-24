#!/usr/bin/env node

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const parseArguments = arguments_ => new Map(arguments_.map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));

const normalizeClause = clause => [...new Set(clause.map(String))].sort();

export function mergeClauseReports(reportPaths) {
  const clauses = new Map();
  for (const rawPath of reportPaths) {
    const path = resolve(rawPath);
    const report = JSON.parse(readFileSync(path, "utf8"));
    const entries = Array.isArray(report) ? report : report.clauses;
    if (!Array.isArray(entries)) throw new Error(`${path} does not contain a clauses array`);
    for (const [index, rawClause] of entries.entries()) {
      if (!Array.isArray(rawClause) || !rawClause.length) {
        throw new Error(`${path} clause ${index} must be a nonempty array`);
      }
      const clause = normalizeClause(rawClause);
      clauses.set(clause.join("|"), clause);
    }
  }
  return [...clauses.values()].sort((left, right) =>
    left.length - right.length || left.join("|").localeCompare(right.join("|"))
  );
}

export function main(arguments_ = process.argv.slice(2)) {
  const args = parseArguments(arguments_);
  const reportPaths = String(args.get("reports") ?? "").split(",").filter(Boolean);
  if (!reportPaths.length) throw new Error("--reports must list at least one clause report");
  if (!args.get("output")) throw new Error("--output is required");
  const output = resolve(args.get("output"));
  const clauses = mergeClauseReports(reportPaths);
  mkdirSync(dirname(output), { recursive: true });
  writeFileSync(output, `${JSON.stringify({
    kind: "polycube_merged_clause_report",
    source_reports: reportPaths.map(path => resolve(path)),
    clauses
  }, null, 2)}\n`);
  process.stdout.write(`${JSON.stringify({ output, source_reports: reportPaths.length, clauses: clauses.length })}\n`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
