import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import fs from 'node:fs';
import dotenv from 'dotenv';

export default defineConfig(({ mode }) => {
  const localEnv = fs.existsSync('local.env') ? dotenv.parse(fs.readFileSync('local.env')) : {};
  const env = { ...localEnv, ...loadEnv(mode, process.cwd(), 'VITE_') };
  return { plugins: [react()], define: { 'import.meta.env.VITE_API_BASE_URL': JSON.stringify(env.VITE_API_BASE_URL || '') } };
});
