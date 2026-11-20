#!/usr/bin/env node
/**
 * Negative controls for the real JetBrains payload: each mutation must be rejected by the
 * named SPEC rule. This is intentionally separate from `npm run conformance` so the gate
 * itself stays green while CI can still prove it would catch a regression.
 */
import { readFileSync } from "node:fs";
import { validatePayload } from "./validate.mjs";

const file = process.argv[2];
if (!file) {
  console.error("usage: negative-control.mjs <payload.json>");
  process.exit(2);
}
const clean = JSON.parse(readFileSync(file, "utf8"));
const clone = (value) => JSON.parse(JSON.stringify(value));
const cases = [
  ["R2", "remove built-in provider", (p) => { p.provider.options = p.provider.options.filter((o) => o.source !== "built-in"); }],
  ["R2", "enable the empty placeholder", (p) => { p.provider.placeholder.disabled = false; }],
  ["R4", "concrete reasoning default", (p) => { p.reasoning.default = "low"; }],
  ["R5", "remove a locale from the matrix", (p) => { p.i18n.files = Object.fromEntries(Object.entries(p.i18n.files).slice(1)); }],
];
let failures = 0;
for (const [rule, name, mutate] of cases) {
  const payload = clone(clean);
  mutate(payload);
  try {
    validatePayload(payload, clean.conformance || { platformLimits: [] });
    console.error(`FAIL ${rule} ${name}: validator accepted the mutation`);
    failures += 1;
  } catch (error) {
    if (error.rule !== rule) {
      console.error(`FAIL ${rule} ${name}: got ${error.rule || error.name}: ${error.message}`);
      failures += 1;
    } else {
      console.log(`OK ${rule} ${name}: ${error.message}`);
    }
  }
}
if (failures) process.exit(1);
console.log(`OK ${cases.length} negative controls rejected`);
