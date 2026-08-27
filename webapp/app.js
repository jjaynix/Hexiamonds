const hexiamonds = APP_DATA.hexiamonds;
const hexListEl = document.getElementById('hex-list');
const groupSelectSection = document.getElementById('group-select-section');
const groupListEl = document.getElementById('group-list');
const timelineEl = document.getElementById('timeline');
const btnPlay = document.getElementById('btn-play');
const btnReset = document.getElementById('btn-reset');
const legendEl = document.getElementById('legend');
const insightEl = document.getElementById('insight');
const hexRotLayer = document.getElementById('hex-rot-layer');
const hexTransLayer = document.getElementById('hex-trans-layer');
const centerLayerHex = document.getElementById('center-layer-hex');

let activeHexId = hexiamonds.find(h => h.found) ? hexiamonds.find(h => h.found).id : hexiamonds[0].id;
let activeGroupIndex = 0;
let isPlaying = false;
let animationFrameId = null;
let currentProgress = 0;
let lastTime = 0;
const DURATION = 18000;
const lattice_V1 = [1.0, 0.0];
const lattice_V2 = [0.5, Math.sqrt(3) / 2];

function currentHex() {
    return hexiamonds.find(h => h.id === activeHexId);
}

function currentGroup() {
    const hex = currentHex();
    if (!hex || !hex.found) return null;
    return hex.groups[activeGroupIndex] || hex.groups[0];
}

function latticeGridToCartesian(q, r) {
    return [q * lattice_V1[0] + r * lattice_V2[0], q * lattice_V1[1] + r * lattice_V2[1]];
}

function buildTileOrder(t1, t2, numImages, numRings) {
    const entries = [];
    for (let i = -numRings; i <= numRings; i++) {
        for (let j = -numRings; j <= numRings; j++) {
            const shell = Math.max(Math.abs(i), Math.abs(j));
            const dx = i * t1[0] + j * t2[0];
            const dy = i * t1[1] + j * t2[1];
            const dist = Math.sqrt(dx * dx + dy * dy);
            for (let k = 0; k < numImages; k++) {
                entries.push({ shell, dist, imageIndex: k, dx, dy });
            }
        }
    }
    entries.sort((a, b) => (a.shell - b.shell) || (a.dist - b.dist) || (a.imageIndex - b.imageIndex));
    return entries;
}

function ringsNeededToCover(t1, t2, halfW, halfH, tileSize) {
    const det = t1[0] * t2[1] - t1[1] * t2[0];
    if (Math.abs(det) < 1e-9) return 16;
    let maxI = 0, maxJ = 0;
    const corners = [[halfW, halfH], [halfW, -halfH], [-halfW, halfH], [-halfW, -halfH]];
    for (const [x, y] of corners) {
        const i = (x * t2[1] - y * t2[0]) / det;
        const j = (t1[0] * y - t1[1] * x) / det;
        maxI = Math.max(maxI, Math.abs(i));
        maxJ = Math.max(maxJ, Math.abs(j));
    }

    const minLen = Math.max(Math.min(Math.hypot(t1[0], t1[1]), Math.hypot(t2[0], t2[1])), 1e-6);
    const margin = (tileSize || 0) / minLen + 1;
    return Math.min(Math.ceil(Math.max(maxI, maxJ) + margin), 24);
}

function tileFootprint(images) {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const img of images) {
        for (const p of img.polygon) {
            if (p[0] < minX) minX = p[0];
            if (p[0] > maxX) maxX = p[0];
            if (p[1] < minY) minY = p[1];
            if (p[1] > maxY) maxY = p[1];
        }
    }
    return Math.max(maxX - minX, maxY - minY, 0.5);
}

function makeLatticeLine(p0, p1) {
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', p0[0]);
    line.setAttribute('y1', p0[1]);
    line.setAttribute('x2', p1[0]);
    line.setAttribute('y2', p1[1]);
    line.setAttribute('class', 'lattice-line');
    return line;
}

function drawTriangularLattice(layer, offset = [0, 0], halfW = 18, halfH = 12) {
    layer.innerHTML = '';
    const frag = document.createDocumentFragment();
    const det = lattice_V1[0] * lattice_V2[1] - lattice_V1[1] * lattice_V2[0];
    let maxQ = 0, maxR = 0;
    const corners = [[halfW, halfH], [halfW, -halfH], [-halfW, halfH], [-halfW, -halfH]];
    for (const [x, y] of corners) {
        const sx = x + offset[0], sy = y + offset[1];
        const q = (sx * lattice_V2[1] - sy * lattice_V2[0]) / det;
        const r = (lattice_V1[0] * sy - lattice_V1[1] * sx) / det;
        maxQ = Math.max(maxQ, Math.abs(q));
        maxR = Math.max(maxR, Math.abs(r));
    }
    const qHalfExtent = Math.ceil(maxQ) + 2;
    const rHalfExtent = Math.ceil(maxR) + 2;
    for (let q = -qHalfExtent; q <= qHalfExtent; q++) {
        for (let r = -rHalfExtent; r <= rHalfExtent; r++) {
            const raw0 = latticeGridToCartesian(q, r);
            const raw1 = latticeGridToCartesian(q + 1, r);
            const raw2 = latticeGridToCartesian(q, r + 1);
            const p0 = [raw0[0] - offset[0], raw0[1] - offset[1]];
            const p1 = [raw1[0] - offset[0], raw1[1] - offset[1]];
            const p2 = [raw2[0] - offset[0], raw2[1] - offset[1]];
            frag.appendChild(makeLatticeLine(p0, p1));
            frag.appendChild(makeLatticeLine(p0, p2));
            frag.appendChild(makeLatticeLine(p1, p2));
        }
    }
    layer.appendChild(frag);
}

function init() {
    buildSidebar();
    selectHexiamond(activeHexId);
    document.getElementById('toggle-lattice').addEventListener('change', e => {
        document.getElementById('lattice-layer-hex').style.display = e.target.checked ? '' : 'none';
    });
    document.getElementById('toggle-center').addEventListener('change', e => {
        centerLayerHex.style.display = e.target.checked ? '' : 'none';
    });
    timelineEl.addEventListener('input', e => {
        currentProgress = parseFloat(e.target.value);
        updateVisuals();
    });
    btnPlay.addEventListener('click', togglePlay);
    btnReset.addEventListener('click', resetAnimation);
}

function buildSidebar() {
    hexiamonds.forEach(hex => {
        const btn = document.createElement('button');
        btn.className = 'hex-btn';
        const badge = hex.found
            ? `<span class="group-badge found">${hex.group}</span>`
            : `<span class="group-badge none">none found</span>`;
        btn.innerHTML = `<strong>${hex.name}</strong><br>${badge}`;
        btn.dataset.id = hex.id;
        btn.addEventListener('click', () => selectHexiamond(hex.id));
        hexListEl.appendChild(btn);
    });
}

function buildGroupSelector(hex) {
    groupListEl.innerHTML = '';
    if (!hex.found || hex.groups.length <= 1) {
        groupSelectSection.style.display = 'none';
        return;
    }
    groupSelectSection.style.display = '';
    hex.groups.forEach((g, idx) => {
        const btn = document.createElement('button');
        btn.className = 'hex-btn';
        const upgradeNote = g.upgraded_from ? ` (found via ${g.upgraded_from})` : '';
        btn.innerHTML = `<strong>${g.group}</strong><br><span class="group-badge found">order ${g.order}</span>${upgradeNote}`;
        btn.dataset.idx = idx;
        btn.addEventListener('click', () => selectGroup(idx));
        groupListEl.appendChild(btn);
    });
}

function selectGroup(idx) {
    activeGroupIndex = idx;
    document.querySelectorAll('#group-list .hex-btn').forEach(btn => {
        btn.classList.toggle('active', parseInt(btn.dataset.idx) === idx);
    });
    buildLegend();
    buildInsight();
    resetAnimation();
}

function selectHexiamond(id) {
    activeHexId = id;
    activeGroupIndex = 0;
    document.querySelectorAll('#hex-list .hex-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.id == id);
    });
    const hex = currentHex();
    buildGroupSelector(hex);
    if (hex.found && hex.groups.length > 1) {
        const firstBtn = groupListEl.querySelector('.hex-btn');
        if (firstBtn) firstBtn.classList.add('active');
    }
    buildLegend();
    buildInsight();
    resetAnimation();
}

function buildLegend() {
    legendEl.innerHTML = '';
    const group = currentGroup();
    if (!group) return;
    const n = group.images.length;
    for (let i = 0; i < n; i++) {
        const item = document.createElement('div');
        item.className = 'legend-item';
        item.textContent = `tile ${i}`;
        legendEl.appendChild(item);
    }
}

function buildInsight() {
    const hex = currentHex();
    const group = currentGroup();
    if (!hex.found || !group) {
        insightEl.textContent = `${hex.name}: no wallpaper group found within the search budget for this shape.`;
        return;
    }
    const mirrorText = group.mirror ? 'contains mirror reflections' : 'no mirror reflections';
    const glideText = group.glide ? 'contains glide reflections independent of any mirror' : 'no independent glide reflections';
    insightEl.textContent = `${hex.name}: viewing ${group.group}, rotation order ${group.order}. ` +
        `${mirrorText}; ${glideText}. Orbit size ${group.orbit_size}`;
}

function resetAnimation() {
    isPlaying = false;
    btnPlay.textContent = 'Play';
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
    currentProgress = 0;
    timelineEl.value = 0;
    updateVisuals();
}

function togglePlay() {
    const group = currentGroup();
    if (!group) return;
    isPlaying = !isPlaying;
    btnPlay.textContent = isPlaying ? 'Pause' : 'Play';
    if (isPlaying) {
        if (currentProgress >= 1) currentProgress = 0;
        lastTime = performance.now();
        animationFrameId = requestAnimationFrame(animationLoop);
    } else {
        cancelAnimationFrame(animationFrameId);
    }
}

function animationLoop(time) {
    if (!isPlaying) return;
    const delta = time - lastTime;
    lastTime = time;
    currentProgress += delta / DURATION;
    if (currentProgress >= 1) {
        currentProgress = 1;
        isPlaying = false;
        btnPlay.textContent = 'Play';
    }
    timelineEl.value = currentProgress;
    updateVisuals();
    if (isPlaying) animationFrameId = requestAnimationFrame(animationLoop);
}

function getPolyString(points) {
    return points.map(p => `${p[0]},${p[1]}`).join(' ');
}

function easeInOut(t) {
    return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
}

function drawTiles(layer, images, tileOrder, progress, centerLayer) {
    layer.innerHTML = '';
    if (centerLayer) centerLayer.innerHTML = '';
    if (tileOrder.length === 0) return;
    const exactIndex = progress * tileOrder.length;
    const revealCount = Math.floor(exactIndex);
    const partial = exactIndex - revealCount;
    const frag = document.createDocumentFragment();
    const centerFrag = centerLayer ? document.createDocumentFragment() : null;
    for (let idx = 0; idx < tileOrder.length; idx++) {
        if (idx > revealCount) break;
        const tile = tileOrder[idx];
        const img = images[tile.imageIndex];
        let alpha = 1.0;
        if (idx === 0) {
            alpha = 1.0;
        } else if (idx === revealCount) {
            alpha = easeInOut(partial);
        }
        if (centerFrag && tile.imageIndex === 0 && alpha > 0.5) {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', tile.dx);
            circle.setAttribute('cy', tile.dy);
            circle.setAttribute('r', 0.16);
            circle.setAttribute('class', 'center-marker');
            centerFrag.appendChild(circle);
        }
        if (alpha <= 0.01) continue;
        const pts = img.polygon.map(p => [p[0] + tile.dx, p[1] + tile.dy]);
        const poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        poly.setAttribute('points', getPolyString(pts));
        poly.setAttribute('class', 'hex-poly');
        poly.setAttribute('fill', '#ffffff');
        poly.setAttribute('fill-opacity', alpha);
        poly.setAttribute('stroke-opacity', alpha);
        frag.appendChild(poly);
    }
    layer.appendChild(frag);
    if (centerFrag) centerLayer.appendChild(centerFrag);
}

let hexCache = { id: null, groupIdx: null, images: null, tiles: null };
let lastGridKey = null;

const canvasHexEl = document.getElementById('canvas-hex');

const ZOOM_TILE_WIDTHS = 2; // lower = bigger tiles nakakalimutan ko lagi

function computeGlobalMaxFootprint() {
    let max = 0;
    for (const hex of hexiamonds) {
        if (!hex.found) continue;
        for (const g of hex.groups) {
            max = Math.max(max, tileFootprint(g.images));
        }
    }
    return max || 1;
}
const GLOBAL_MAX_FOOTPRINT = computeGlobalMaxFootprint();

function getPanelAspect(svgEl) {
    const rect = svgEl.getBoundingClientRect();
    if (!rect.width || !rect.height) return 1;
    return rect.width / rect.height;
}

function applyViewBox(svgEl, halfW, halfH) {
    svgEl.setAttribute('viewBox', `${-halfW} ${-halfH} ${2 * halfW} ${2 * halfH}`);
}

function updateVisuals() {
    const hex = currentHex();
    const group = currentGroup();
    if (!hex || !group) {
        hexTransLayer.innerHTML = '';
        hexRotLayer.innerHTML = '';
        return;
    }
    const gridKey = hex.id + ':' + activeGroupIndex;
    if (lastGridKey !== gridKey) {
        const aspect = getPanelAspect(canvasHexEl);
        const halfBase = GLOBAL_MAX_FOOTPRINT * ZOOM_TILE_WIDTHS;
        const hexHalfW = aspect >= 1 ? halfBase * aspect : halfBase;
        const hexHalfH = aspect >= 1 ? halfBase : halfBase / aspect;
        const hexRings = ringsNeededToCover(group.t1, group.t2, hexHalfW, hexHalfH, tileFootprint(group.images));
        hexCache = { id: hex.id, groupIdx: activeGroupIndex, images: group.images, tiles: buildTileOrder(group.t1, group.t2, group.images.length, hexRings) };

        drawTriangularLattice(document.getElementById('lattice-layer-hex'), group.center, hexHalfW, hexHalfH);
        applyViewBox(canvasHexEl, hexHalfW, hexHalfH);
        lastGridKey = gridKey;
    }

    drawTiles(hexTransLayer, hexCache.images, hexCache.tiles, currentProgress, centerLayerHex);
    hexRotLayer.innerHTML = '';
}

init();