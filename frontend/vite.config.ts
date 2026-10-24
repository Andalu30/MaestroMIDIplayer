import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit({
			preprocess: vitePreprocess(),
			adapter: adapter({ pages: 'build', assets: 'build', fallback: 'index.html' }),
			// Docker builds with a placeholder base that the backend rewrites at
			// startup from MAESTRO_BASE_PATH (subfolder hosting); local builds use root
			paths: {
				base: (process.env.MAESTRO_BUILD_BASE ?? '') as '' | `/${string}`,
				relative: false
			}
		})
	],
	server: {
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true,
				ws: true
			}
		}
	}
});
