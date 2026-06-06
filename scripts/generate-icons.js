const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const publicDir = path.join(__dirname, '..', 'public');
const svgPath = path.join(publicDir, 'favicon.svg');

async function generateIcons() {
  const svgBuffer = fs.readFileSync(svgPath);
  
  await sharp(svgBuffer, { density: 300 })
    .resize(192, 192)
    .png()
    .toFile(path.join(publicDir, 'icon-192x192.png'));
  
  console.log('Generated icon-192x192.png');

  await sharp(svgBuffer, { density: 300 })
    .resize(512, 512)
    .png()
    .toFile(path.join(publicDir, 'icon-512x512.png'));
  
  console.log('Generated icon-512x512.png');
}

generateIcons().catch(console.error);
