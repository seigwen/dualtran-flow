#!/usr/bin/env node
// Sort the generated payload with the same Intl.Collator the validator uses.
// The Kotlin model owns the data; this step only canonicalises presentation order.
import { readFileSync, writeFileSync } from "node:fs";

const file = process.argv[2];
if (!file) {
  console.error("usage: sort-payload.mjs <payload.json>");
  process.exit(2);
}
const payload = JSON.parse(readFileSync(file, "utf8"));
const collator = new Intl.Collator("en", { numeric: true, sensitivity: "base" });

function byLabel(left, right) {
  return collator.compare(String(left.label ?? ""), String(right.label ?? ""));
}

function sortOptions(options) {
  if (!Array.isArray(options)) return options;
  const custom = options.filter((option) => option.source === "custom" || /^__custom/i.test(String(option.value ?? "")));
  const normal = options.filter((option) => !custom.includes(option));
  normal.sort(byLabel);
  return [...normal, ...custom.sort(byLabel)];
}

if (payload.provider?.options) payload.provider.options = sortOptions(payload.provider.options);
for (const key of Object.keys(payload.model?.byProvider ?? {})) {
  payload.model.byProvider[key] = sortOptions(payload.model.byProvider[key]);
}
if (payload.model?.options) payload.model.options = sortOptions(payload.model.options);
writeFileSync(file, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
console.log(JSON.stringify(payload, null, 2));
