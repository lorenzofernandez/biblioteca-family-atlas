import{test}from'node:test';import assert from'node:assert/strict';import fs from'node:fs';
test('snapshot contains full source data and biography dictionaries',()=>{const authors=JSON.parse(fs.readFileSync('public/archive/authors-data.json'));assert(authors.authors.length>21000);assert.equal(fs.readdirSync('public/archive/biographies-it').filter(f=>f.endsWith('.json')).length,256)});
