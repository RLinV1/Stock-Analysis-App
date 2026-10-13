export type Colors = {
  bg: string;
  surface: string;
  text: string;
  secondary: string;
  accent: string;
  onAccent: string;
  border: string;
  muted: string;
  error: string;
};

// Opaque grouped surfaces stay legible in both appearances without relying on blur.
export const light: Colors = {
  bg: '#F2F2F7', surface: '#FFFFFF', text: '#1C1C1E', secondary: '#595B64',
  accent: '#005CC8', onAccent: '#FFFFFF', border: '#D1D1D6', muted: '#E8E8ED', error: '#B4232C',
};

export const dark: Colors = {
  bg: '#101012', surface: '#1C1C1E', text: '#F5F5F7', secondary: '#B8BBC5',
  accent: '#8FBCFF', onAccent: '#102441', border: '#414147', muted: '#2C2C30', error: '#FFB4B4',
};
