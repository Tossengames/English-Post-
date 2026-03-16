import puppeteer from 'puppeteer';
import { writeFileSync } from 'fs';

const SITE_URL = 'https://tossengames.github.io/English-Post-/';
const WAIT = 40000;

const browser = await puppeteer.launch({
  headless: true,
  args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--autoplay-policy=no-user-gesture-required'],
});

const page = await browser.newPage();
page.on('console', () => {});
await page.goto(SITE_URL, { waitUntil: 'networkidle2', timeout: 60000 });

try {
  await page.waitForFunction(() => window.STILL_META !== null && window.STILL_META.url, { timeout: WAIT });
} catch {
  console.error('Timed out');
  await browser.close();
  process.exit(1);
}

const meta = await page.evaluate(() => window.STILL_META);
await browser.close();

console.log('url:', meta.url);
console.log('start:', meta.start);
console.log('clip:', meta.clipDuration);

writeFileSync(process.env.GITHUB_OUTPUT,
  `VIDEO_URL=${meta.url}\nSTART_TIME=${meta.start}\nCLIP_DURATION=${meta.clipDuration}\n`,
  { flag: 'a' }
);