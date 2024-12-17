import fs from 'fs';
import path from 'path';

export type ImageMap = Record<string, string>;

export function generateImageMap(subDir?: string): ImageMap {
    const baseDir = path.join(process.cwd(), 'public');
    const imageDir = subDir ? path.join(baseDir, subDir) : baseDir;
    const files = fs.readdirSync(imageDir);

    const imageMap: ImageMap = {};
    files.forEach((file) => {
        const name = file.replace(/\.[^/.]+$/, ''); // Remove the extension
        imageMap[name] = subDir ? `/${subDir}/${file}` : `/${file}`; // Map kebab-case name to its path
    });

    return imageMap;
}
