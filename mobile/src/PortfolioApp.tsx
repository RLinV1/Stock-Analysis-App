import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import { BackHandler, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, useColorScheme, View } from 'react-native';

type Page = 'experiments' | 'new' | 'detail' | 'results';
type Colors = { bg: string; surface: string; text: string; secondary: string; accent: string; onAccent: string; border: string; muted: string; error: string };
const light: Colors = { bg: '#F3F5F8', surface: '#FFFFFF', text: '#182437', secondary: '#45566C', accent: '#174EA6', onAccent: '#FFFFFF', border: '#D6DFE8', muted: '#E8EDF3', error: '#A4262C' };
const dark: Colors = { bg: '#101923', surface: '#1A2837', text: '#F5F7FA', secondary: '#C4D0DE', accent: '#A4C8FF', onAccent: '#102641', border: '#38506A', muted: '#26394B', error: '#FFB4B4' };

function Action({ label, onPress, colors, disabled = false, quiet = false }: { label: string; onPress: () => void; colors: Colors; disabled?: boolean; quiet?: boolean }) {
  return <Pressable accessibilityRole="button" accessibilityLabel={label} disabled={disabled} onPress={onPress} style={({ pressed }) => [styles.action, { backgroundColor: disabled ? colors.muted : quiet ? colors.surface : colors.accent, borderColor: quiet ? colors.border : 'transparent', opacity: pressed ? 0.72 : 1 }]}>
    <Text style={[styles.actionText, { color: disabled ? colors.secondary : quiet ? colors.text : colors.onAccent }]}>{label}</Text>
  </Pressable>;
}

function Card({ children, colors }: { children: React.ReactNode; colors: Colors }) {
  return <View style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }]}>{children}</View>;
}

function integerInRange(value: string, min: number, max: number) {
  return /^\d+$/.test(value) && Number(value) >= min && Number(value) <= max;
}

export default function PortfolioApp() {
  const isDark = useColorScheme() === 'dark';
  const colors = isDark ? dark : light;
  const [stack, setStack] = useState<Page[]>(['experiments']);
  const [lookback, setLookback] = useState('50');
  const [epochs, setEpochs] = useState('3');
  const [edited, setEdited] = useState({ lookback: false, epochs: false });
  const page = stack[stack.length - 1];
  const back = () => setStack((current) => current.length > 1 ? current.slice(0, -1) : current);
  const open = (next: Page) => setStack((current) => [...current, next]);

  useEffect(() => {
    if (Platform.OS !== 'android' || stack.length === 1) return;
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => { back(); return true; });
    return () => subscription.remove();
  }, [stack.length]);

  const title = { experiments: 'Experiments', new: 'New experiment', detail: 'Experiment detail', results: 'Results' }[page];
  const text = (value: string, secondary = false) => <Text style={[styles.body, { color: secondary ? colors.secondary : colors.text }]}>{value}</Text>;

  return <View style={[styles.root, { backgroundColor: colors.bg }]}>
    <StatusBar style={isDark ? 'light' : 'dark'} />
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      {stack.length > 1 && <View style={styles.backRow}><Action label="Back" onPress={back} colors={colors} quiet /></View>}
      <Text style={[styles.eyebrow, { color: colors.accent }]}>PORTFOLIO LAB</Text>
      <Text accessibilityRole="header" style={[styles.title, { color: colors.text }]}>{title}</Text>
      <Text style={[styles.subheading, { color: colors.secondary }]}>Research workspace · local preview</Text>

      {page === 'experiments' && <>
        <Card colors={colors}>
          <Text style={[styles.cardTitle, { color: colors.text }]}>Synthetic demonstration</Text>
          {text('Explore how a research run will look. This is sample content, not a submitted job or a historical result.', true)}
          <Action label="Open demo experiment" onPress={() => open('detail')} colors={colors} />
        </Card>
        <Card colors={colors}>
          <Text style={[styles.cardTitle, { color: colors.text }]}>No live experiments yet</Text>
          {text('The research service is not connected. You can inspect the planned settings, but cannot start a run yet.', true)}
          <Action label="New experiment" onPress={() => open('new')} colors={colors} quiet />
        </Card>
      </>}

      {page === 'new' && <Card colors={colors}>
        <Text style={[styles.cardTitle, { color: colors.text }]}>Preview settings</Text>
        {text('Synthetic sample · LSTM research baseline. These fields are a local preview; no experiment will be sent.', true)}
        <Text style={[styles.fieldLabel, { color: colors.text }]}>Lookback days</Text>
        <TextInput accessibilityLabel="Lookback days" keyboardType="number-pad" onBlur={() => setEdited((current) => ({ ...current, lookback: true }))} onChangeText={setLookback} style={[styles.input, { borderColor: colors.border, color: colors.text, backgroundColor: colors.bg }]} value={lookback} />
        {edited.lookback && !integerInRange(lookback, 10, 100) && <Text accessibilityRole="alert" style={[styles.error, { color: colors.error }]}>Lookback must be a whole number from 10 to 100.</Text>}
        <Text style={[styles.fieldLabel, { color: colors.text }]}>Training epochs</Text>
        <TextInput accessibilityLabel="Training epochs" keyboardType="number-pad" onBlur={() => setEdited((current) => ({ ...current, epochs: true }))} onChangeText={setEpochs} style={[styles.input, { borderColor: colors.border, color: colors.text, backgroundColor: colors.bg }]} value={epochs} />
        {edited.epochs && !integerInRange(epochs, 1, 5) && <Text accessibilityRole="alert" style={[styles.error, { color: colors.error }]}>Epochs must be a whole number from 1 to 5 for this preview.</Text>}
        <View style={styles.gap} />
        <Action label="Start experiment" onPress={() => {}} colors={colors} disabled />
        <Text style={[styles.helper, { color: colors.secondary }]}>Start unavailable: the service is not connected. No job is queued.</Text>
      </Card>}

      {page === 'detail' && <Card colors={colors}>
        <Text style={[styles.cardTitle, { color: colors.text }]}>Synthetic preview</Text>
        {text('Model: 64-unit LSTM · Dataset: synthetic sample · Status: preview only.', true)}
        {text('No job ID exists. No worker is running. Cancellation is unavailable for sample content.', true)}
        <Action label="View results" onPress={() => open('results')} colors={colors} />
      </Card>}

      {page === 'results' && <>
        <Card colors={colors}>
          <Text style={[styles.cardTitle, { color: colors.text }]}>Report preview · synthetic data</Text>
          {text('No measured run is loaded. Performance and allocations are unavailable until a real experiment finishes.', true)}
        </Card>
        <Card colors={colors}>
          <Text style={[styles.cardTitle, { color: colors.text }]}>Comparison</Text>
          {text('LSTM Sharpe ratio: unavailable — no measured run.')}
          {text('Equal-weight baseline Sharpe ratio: unavailable — no measured run.')}
          {text('Both strategies must use identical dates and costs before a number appears here.', true)}
        </Card>
        <Text style={[styles.notice, { color: colors.secondary }]}>Research only. Not investment advice. Historical examples do not predict future returns.</Text>
      </>}
    </ScrollView>
  </View>;
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  content: { flexGrow: 1, width: '100%', maxWidth: 720, alignSelf: 'center', paddingHorizontal: 20, paddingTop: Platform.OS === 'android' ? 48 : 32, paddingBottom: 48 },
  backRow: { alignSelf: 'flex-start', marginBottom: 20 },
  eyebrow: { fontSize: 12, fontWeight: '700', letterSpacing: 1.5, marginBottom: 8 },
  title: { fontSize: 34, lineHeight: 40, fontWeight: '700' },
  subheading: { fontSize: 14, lineHeight: 21, marginTop: 6, marginBottom: 24 },
  card: { borderWidth: 1, borderRadius: 20, padding: 20, marginBottom: 16 },
  cardTitle: { fontSize: 20, lineHeight: 27, fontWeight: '700', marginBottom: 8 },
  body: { fontSize: 16, lineHeight: 24, marginBottom: 8 },
  gap: { height: 10 },
  action: { minHeight: 52, borderRadius: 14, borderWidth: 1, paddingHorizontal: 18, justifyContent: 'center', alignItems: 'center', marginTop: 10 },
  actionText: { fontSize: 16, lineHeight: 22, fontWeight: '600', textAlign: 'center' },
  fieldLabel: { fontSize: 15, fontWeight: '600', marginTop: 16, marginBottom: 8 },
  input: { minHeight: 52, borderWidth: 1, borderRadius: 12, paddingHorizontal: 14, fontSize: 16 },
  error: { fontSize: 14, lineHeight: 21, marginTop: 6 },
  helper: { fontSize: 14, lineHeight: 21, marginTop: 12 },
  notice: { fontSize: 14, lineHeight: 21, marginTop: 4 },
});
