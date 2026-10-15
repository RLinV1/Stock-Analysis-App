import { useWindowDimensions } from 'react-native';

// Native Text keeps its default font scaling. Only surrounding layout changes here.
export function useReadableLayout() {
  const { width, fontScale } = useWindowDimensions();
  const spacingScale = Math.min(Math.max(fontScale, 1), 2);
  return {
    stacked: width < 400 || fontScale >= 1.5,
    cardPadding: width < 400 ? 16 : 22,
    contentPadding: width < 400 ? 16 : 20,
    gap: 16 * spacingScale,
  };
}
