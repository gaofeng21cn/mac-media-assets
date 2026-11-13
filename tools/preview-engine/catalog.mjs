// All browser entry points apply the same exact-version withdrawal register.
export function effectiveRows(rows, curation) {
  return rows.map(row => {
    const decision = curation.assets[row.id] || row.curation;
    const boundary={...row.review_boundary, ...decision?.review_boundary};
    if(row.delivery?.encoding_review==='pending'){
      boundary.encoding='pending';
      for(const field of ['static','motion','listening'])if(boundary[field]&&boundary[field]!=='not_applicable')boundary[field]='pending';
    }
    return {...row, curation: decision, review_boundary: boundary};
  });
}
export function available(row) {
  return !['superseded', 'needs_rebuild'].includes(row.curation?.status)
    && row.review_boundary?.admission !== 'reference_only';
}
export async function loadCatalog(root) {
  const [catalog, curation] = await Promise.all([
    fetch(new URL('catalog/assets.jsonl', root)),
    fetch(new URL('collections/curation.json', root))
  ]);
  if (!catalog.ok || !curation.ok) throw new Error('素材登记不可读取');
  const decisions = await curation.json();
  if (!decisions || typeof decisions.assets !== 'object' || !decisions.assets || Array.isArray(decisions.assets) || Object.values(decisions.assets).some(d => !d || typeof d !== 'object' || Array.isArray(d) || (d.review_boundary && (typeof d.review_boundary !== 'object' || Array.isArray(d.review_boundary))))) throw new Error('策展登记无效');
  return effectiveRows((await catalog.text()).trim().split('\n').filter(Boolean).map(JSON.parse), decisions);
}
