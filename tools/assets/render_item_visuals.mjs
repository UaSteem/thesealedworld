// Rasterize authored SVGs; JSON is only build-tool transport, never a server catalog.
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import path from 'node:path';

const require = createRequire(import.meta.url);
const sharp = require(process.env.ITEM_ART_SHARP_MODULE || 'sharp');
const chunks = [];
for await (const chunk of process.stdin) chunks.push(chunk);
const input = JSON.parse(Buffer.concat(chunks).toString('utf8'));
const output = {};
for (const variant of input.variants) {
  const svg = await readFile(path.join(input.root, variant.source_path));
  const renditions = {};
  for (const [kind, width, height] of [['thumbnail', 96, 288], ['image', 256, 768]]) {
    const content = await sharp(svg, { density: 576 })
      .resize(width, height, { fit: 'contain', background: '#00000000' })
      .webp({ lossless: true, effort: 6 })
      .toBuffer();
    const digest = createHash('sha256').update(content).digest('hex');
    const key = `items/sword/${variant.visual_variant_id}/${digest}.${kind}.webp`;
    const destination = path.join(input.output, key);
    await mkdir(path.dirname(destination), { recursive: true });
    await writeFile(destination, content);
    renditions[kind] = {
      storage_key: key, sha256: digest, width, height, content_type: 'image/webp',
    };
  }
  output[variant.visual_variant_id] = renditions;
}
process.stdout.write(JSON.stringify(output));
