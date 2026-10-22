import {createGeographyLayout} from './cards-geography-layout.mjs?v=18';
// One stable position per catalogue record, in every view.
function fittedStep(count, width, height) {
  let low = 0, high = Math.min(width, height);
  for (let i = 0; i < 40; i++) {
    const step = (low + high) / 2;
    if (Math.floor(width / step) * Math.floor(height / step) >= count) low = step;
    else high = step;
  }
  return low;
}

export const timelineRowGap = height => Math.min(height * .38, 280);

// Pack the current matches into the largest equal squares that fit the viewport.
export function createFilteredWallLayout({width, height, ids, base}) {
  const positions = base.slice();
  if (!ids.length) return positions;
  const step = fittedStep(ids.length, width * .97, height * .95);
  const columns = Math.min(ids.length, Math.max(1, Math.floor(width * .97 / step)));
  const rows = Math.ceil(ids.length / columns);
  const gap = step > 24 ? Math.min(16, step * .08) : step * .25;
  ids.forEach((id, rank) => {
    const row = Math.floor(rank / columns);
    const rowCount = Math.min(columns, ids.length - row * columns);
    positions.set([
      (width - rowCount * step) / 2 + (rank % columns + .5) * step,
      (height - rows * step) / 2 + (row + .5) * step,
      step - gap,
    ], id * 3);
  });
  return positions;
}

export function createSquareLayouts({width, height, records, wallIds, grid, eras, geography}) {
  const total = records.length;
  const layouts = Array.from({length: 4}, () => new Float32Array(total * 3));
  const byEra = new Map([...eras, null].map(era => [era, []]));
  const rare = [], unknown = [];
  records.forEach((record, id) => {
    const era = record.year == null ? null : Math.floor(record.year / 100) * 100;
    (byEra.get(era) || byEra.get(null)).push(id);
    (record.rare ? rare : unknown).push(id);
  });
  const compare = (a, b) => (records[a].year || 0) - (records[b].year || 0)
    || records[a].file.localeCompare(records[b].file) || records[a].page - records[b].page;
  byEra.forEach(ids => ids.sort(compare));
  rare.sort(compare); unknown.sort(compare);
  const put = (layout, id, x, y, size) => layout.set([x, y, size], id * 3);
  wallIds.forEach((id, cell) => {
    if (id < 0 || id >= total) throw Error('A square is missing its catalogue record');
    const x = (width - grid.columns * grid.cell) / 2 + (cell % grid.columns + .5) * grid.cell;
    const y = (height - grid.rows * grid.cell) / 2 + (Math.floor(cell / grid.columns) + .5) * grid.cell;
    put(layouts[0], id, x, y, grid.cell * .65);
    put(layouts[3], id, x, y, grid.cell * .65);
  });

  const mobile = width < 751;
  const baseline = height * .77, plotHeight = height * (mobile ? .33 : .38);
  const spineGap = mobile ? 38 : 64, sideWidth = width * .47 - spineGap;
  const bandHeight = Math.min(height * .15, mobile ? 80 : 120), rowGap = timelineRowGap(height);
  const rowCenters = [...byEra.keys()].map((_, group) => height * .94 + group * rowGap);
  const largest = Math.max(...[...byEra.values()].map(ids => ids.length));
  const timeStep = fittedStep(Math.ceil(largest / 2), sideWidth, bandHeight);
  const timeRows = Math.max(1, Math.floor(bandHeight / timeStep));
  const timeColumns = Math.max(1, Math.floor(sideWidth / timeStep));
  [...byEra.values()].forEach((ids, group) => {
    const halfCount = Math.ceil(ids.length / 2);
    // Keep small cohorts horizontal too, using the same square size for every card.
    const rows = Math.max(1, Math.ceil(halfCount / timeColumns),
      Math.min(timeRows, Math.round(Math.sqrt(halfCount * bandHeight / sideWidth))));
    ids.forEach((id, rank) => {
      const slot = Math.floor(rank / 2), side = rank % 2 === 0 ? -1 : 1;
      put(layouts[1], id,
        width / 2 + side * (spineGap + (Math.floor(slot / rows) + .5) * timeStep),
        rowCenters[group] + (slot % rows - (rows - 1) / 2) * timeStep, timeStep * .68);
    });
  });

  const geo = createGeographyLayout({width,height,records,geography});
  layouts[2] = geo.positions;
  const timeline = {
    rowCenters, spineGap,
    maxPan: rowCenters.at(-1) - height * .5,
    worldHeight: rowCenters.at(-1) + bandHeight / 2,
  };
  return {layouts, byEra, rare, unknown, timeline, geography:geo};
}
