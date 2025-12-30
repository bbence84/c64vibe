import sharp from 'sharp';

export interface RGB { r: number; g: number; b: number; }

const BLACK: RGB = { r: 0, g: 0, b: 0 };
const WHITE: RGB = { r: 255, g: 255, b: 255 };

export async function extractAlphaTwoPass(
  imgOnWhitePath: string,
  
  imgOnBlackPath: string,
  outputPath: string
): Promise<void> {
  const img1 = sharp(imgOnWhitePath);
  const img2 = sharp(imgOnBlackPath);

  // Ensure we are working with raw pixel data
  const { data: dataWhite, info: meta } = await img1
    .ensureAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });
    
  const { data: dataBlack } = await img2
    .ensureAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });

  if (dataWhite.length !== dataBlack.length) {
    throw new Error("Dimension mismatch: Images must be identical size");
  }

  const outputBuffer = Buffer.alloc(dataWhite.length);

  // Distance between White (255,255,255) and Black (0,0,0)
  // sqrt(255^2 + 255^2 + 255^2) ≈ 441.67
  const bgDist = Math.sqrt(3 * 255 * 255);

  for (let i = 0; i < meta.width * meta.height; i++) {
    const offset = i * 4;

    // Get RGB values for the same pixel in both images
    const rW = dataWhite[offset];
    const gW = dataWhite[offset + 1];
    const bW = dataWhite[offset + 2];

    const rB = dataBlack[offset];
    const gB = dataBlack[offset + 1];
    const bB = dataBlack[offset + 2];

    // Calculate the distance between the two observed pixels
    const pixelDist = Math.sqrt(
      Math.pow(rW - rB, 2) +
      Math.pow(gW - gB, 2) +
      Math.pow(bW - bB, 2)
    );

    // THE FORMULA:
    // If the pixel is 100% opaque, it looks the same on Black and White (pixelDist = 0).
    // If the pixel is 100% transparent, it looks exactly like the backgrounds (pixelDist = bgDist).
    // Therefore:
    let alpha = 1 - (pixelDist / bgDist);
    
    // Clamp results to 0-1 range
    alpha = Math.max(0, Math.min(1, alpha));

    // Color Recovery:
    // We use the image on black to recover the color, dividing by alpha 
    // to un-premultiply it (brighten the semi-transparent pixels)
    let rOut = 0, gOut = 0, bOut = 0;

    if (alpha > 0.01) {
       // Recover foreground color from the version on black
       // (C - (1-alpha) * BG) / alpha
       // Since BG is black (0,0,0), this simplifies to C / alpha
       rOut = rB / alpha;
       gOut = gB / alpha;
       bOut = bB / alpha;
    }

    outputBuffer[offset] = Math.round(Math.min(255, rOut));
    outputBuffer[offset + 1] = Math.round(Math.min(255, gOut));
    outputBuffer[offset + 2] = Math.round(Math.min(255, bOut));
    outputBuffer[offset + 3] = Math.round(alpha * 255);
  }

  await sharp(outputBuffer, { 
    raw: { width: meta.width, height: meta.height, channels: 4 } 
  })
  .png()
  .toFile(outputPath);
  
  console.log(`✅ Alpha extraction complete! Saved to: ${outputPath}`);
}

// Main execution block
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length !== 3) {
    console.error('Usage: npx tsx extract_alpha.ts <img-on-white> <img-on-black> <output-path>');
    console.error('Example: npx tsx extract_alpha.ts logo_light.jpg logo_dark.jpg output.png');
    process.exit(1);
  }
  
  const [imgOnWhite, imgOnBlack, outputPath] = args;
  
  console.log('🔍 Extracting alpha channel...');
  console.log(`   White background: ${imgOnWhite}`);
  console.log(`   Black background: ${imgOnBlack}`);
  console.log(`   Output: ${outputPath}`);
  
  extractAlphaTwoPass(imgOnWhite, imgOnBlack, outputPath)
    .then(() => {
      console.log('✨ Done!');
    })
    .catch((error) => {
      console.error('❌ Error:', error.message);
      process.exit(1);
    });
}