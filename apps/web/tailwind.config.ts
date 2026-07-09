import type { Config } from "tailwindcss";
import designTokensPreset from "@rtas/design-tokens/tailwind";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  corePlugins: {
    preflight: false,
  },
  presets: [designTokensPreset],
  theme: {
    extend: {},
  },
  plugins: [require("@tailwindcss/typography")],
};

export default config;
