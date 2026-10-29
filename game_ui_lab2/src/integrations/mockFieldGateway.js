// Precomputed visual responses; no damage formula or combat resolver in the client.
const snapshots=[{hp:.52},{hp:.44},{hp:.35},{hp:.26},{hp:.18},{hp:.10}];
export function createMockFieldGateway(){let index=0;return {exchange(){const snapshot=snapshots[Math.min(index++,snapshots.length-1)];return structuredClone(snapshot);}};}
