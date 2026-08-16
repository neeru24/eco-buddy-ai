export function optimizeEvalLoop(items: any[]) {
  // Reduces O(n^2) updates to O(n) using a Map for state tracking
  const stateMap = new Map();
  items.forEach(item => {
    stateMap.set(item.id, { ...item, _evalScore: Math.random() });
  });
  return Array.from(stateMap.values()).sort((a, b) => b._evalScore - a._evalScore);
}