"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync("web/index.html", "utf8");
const match = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(match, "web app must contain a script");
const script = match[1].replace('"sample").click();', '"sample").click();');
// Stub the page controls only; exercise production calculator and parser.
const elements = new Map();
const sandbox = {
  document: {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, {addEventListener(){}, click(){}});
      return elements.get(id);
    },
  },
  console,
  Number,
  Map,
  Set,
  Math,
};
vm.createContext(sandbox);
new vm.Script(script, {filename: "web/index.html"}).runInContext(sandbox);
const evalJs = expr => vm.runInContext(expr, sandbox);

test("Two-arm reference values match Python hand calculation", () => {
  const result = evalJs('calculate(parseData(example),10)');
  assert.ok(Math.abs(result.groups.A.rmst - 6.8) < 1e-10);
  assert.ok(Math.abs(result.groups.B.rmst - 7.8) < 1e-10);
  assert.ok(Math.abs(result.contrast.difference - 1) < 1e-10);
});

test("Events at tied censoring times use full risk set", () => {
  const result = evalJs('calculate(parseData("time,event\\n2,1\\n2,0\\n4,1"),4)');
  assert.ok(Math.abs(result.groups.All.rmst - (2+4/3)) < 1e-10);
});

test("Quoted CSV values and TSV parsing", () => {
  const csv = evalJs('parseData("time,event,group\\n2,1,\\\"A, B\\\"\\n4,0,\\\"A, B\\\"")');
  assert.equal(csv[0].group, "A, B");
  const tsv = evalJs('parseData("time\\tevent\\n2\\t1\\n4\\t0")');
  assert.equal(tsv.length, 2);
});

test("Bad time, invalid event, unobserved tau are rejected", () => {
  assert.throws(() => evalJs('calculate(parseData("time,event\\n1,1"),2)'), /exceeds/);
  assert.throws(() => evalJs('parseData("time,event\\n-1,1")'), /negative/);
  assert.throws(() => evalJs('parseData("time,event\\n2,3")'), /event/);
  assert.throws(() => evalJs('parseData("time,event\\n2,1,extra")'), /fields/);
});

test("All censoring gives RMST equal to tau", () => {
  assert.equal(evalJs('calculate(parseData("time,event\\n2,0\\n5,0"),5).groups.All.rmst'), 5);
});
