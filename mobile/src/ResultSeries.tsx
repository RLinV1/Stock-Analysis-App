import { useCallback, useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { RunsApiError, validateAllocationContext, validateEquityContext } from './api/client';
import type { RunsClient } from './api/client';
import type { Allocations, RunReport } from './api/contract';
import type { Colors } from './theme';

const strategyName = (name: string) => ({ lstm: 'LSTM', equal_weight: 'Equal weight', stock_bond_60_40: '60/40 stocks & bonds' }[name] ?? name);

function failure(error: unknown) {
  if (error instanceof RunsApiError) {
    if (error.kind === 'invalid_response') return 'Result data is invalid or does not match this report. No values are shown.';
    if (error.kind === 'http') return `The service returned HTTP ${error.status ?? 'error'}. No values are shown.`;
    if (error.kind === 'timeout') return 'The service did not respond in time. Retry when ready.';
  }
  return 'Result data could not be loaded. Check the connection and retry.';
}

function useResult<T>(load: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const sequence = useRef(0);
  const reload = useCallback(async () => {
    const seq = ++sequence.current;
    setData(null); setError(null); setLoading(true);
    try {
      const result = await load();
      if (seq === sequence.current) setData(result);
    } catch (caught) {
      if (seq === sequence.current) setError(failure(caught));
    } finally {
      if (seq === sequence.current) setLoading(false);
    }
  }, [load]);
  useEffect(() => {
    void reload();
    return () => { sequence.current++; };
  }, [reload]);
  return { data, error, loading, reload };
}

function Control({ label, onPress, colors, disabled = false, selected }: { label: string; onPress: () => void; colors: Colors; disabled?: boolean; selected?: boolean }) {
  return <Pressable accessibilityRole="button" accessibilityLabel={label} accessibilityState={{ disabled, ...(selected === undefined ? {} : { selected }) }} disabled={disabled} onPress={onPress} style={({ pressed }) => [styles.control, { borderColor: selected ? colors.accent : colors.border, backgroundColor: selected ? colors.muted : colors.surface, opacity: disabled ? 0.5 : pressed ? 0.72 : 1 }]}>
    <Text style={[styles.controlText, { color: colors.text }]}>{label}</Text>
  </Pressable>;
}

function Curve({ wealth, colors, name }: { wealth: number[]; colors: Colors; name: string }) {
  const [width, setWidth] = useState(0);
  // Normalize before subtraction so extreme finite inputs cannot overflow the range.
  const scale = Math.max(...wealth.map(Math.abs), 1);
  const values = wealth.map((value) => value / scale);
  const low = Math.min(...values), high = Math.max(...values);
  const y = (value: number) => high === low ? 80 : 8 + (high - value) / (high - low) * 144;
  const x = (index: number) => values.length === 1 ? width / 2 : index / (values.length - 1) * width;
  return <>
    <Text style={[styles.caption, { color: colors.secondary }]}>{`Wealth range ${Math.min(...wealth).toFixed(4)}–${Math.max(...wealth).toFixed(4)}`}</Text>
    <View accessible accessibilityRole="image" accessibilityLabel={`${name} equity curve. Exact values for each date are available using Previous date and Next date below.`} onLayout={(event) => setWidth(event.nativeEvent.layout.width)} style={[styles.plot, { borderColor: colors.border }]}>
      {width > 0 && values.map((value, index) => {
        if (index === 0) return <View key="first" style={[styles.dot, { left: x(0) - 3, top: y(value) - 3, backgroundColor: colors.accent }]} />;
        const fromX = x(index - 1), fromY = y(values[index - 1]);
        const dx = x(index) - fromX, dy = y(value) - fromY;
        const length = Math.hypot(dx, dy);
        return <View key={index} style={[styles.segment, { backgroundColor: colors.accent, width: length, left: (fromX + x(index)) / 2 - length / 2, top: (fromY + y(value)) / 2 - 1, transform: [{ rotate: `${Math.atan2(dy, dx)}rad` }] }]} />;
      })}
    </View>
  </>;
}

function Weights({ allocations, strategy, dateIndex, colors }: { allocations: Allocations; strategy: string; dateIndex: number; colors: Colors }) {
  const row = allocations.strategies.find((item) => item.strategy === strategy)!.rows[dateIndex];
  return <>
    {allocations.assets.map((asset, i) => <View key={asset} style={styles.weight}>
      <Text style={[styles.value, { color: colors.text }]}>{`${asset}: ${(row.weights[i] * 100).toFixed(2)}%`}</Text>
      <View accessible={false} style={[styles.track, { backgroundColor: colors.muted }]}><View style={[styles.fill, { width: `${row.weights[i] * 100}%`, backgroundColor: colors.accent }]} /></View>
    </View>)}
  </>;
}

export function ResultSeries({ client, runId, report, colors }: { client: RunsClient; runId: string; report: RunReport; colors: Colors }) {
  const loadEquity = useCallback(async () => validateEquityContext(await client.equityCurve(runId), report), [client, runId, report]);
  const loadAllocations = useCallback(async () => validateAllocationContext(await client.allocations(runId), report), [client, runId, report]);
  const equity = useResult(loadEquity), allocations = useResult(loadAllocations);
  const strategies = Object.keys(report.strategies);
  const [strategy, setStrategy] = useState(strategies[0]);
  const [dateIndex, setDateIndex] = useState(report.testDates.length - 1);
  return <View style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }]}>
    <Text style={[styles.kicker, { color: colors.accent }]}>SYNTHETIC SERIES</Text>
    <Text accessibilityRole="header" style={[styles.title, { color: colors.text }]}>Equity & allocations</Text>
    <Text style={[styles.body, { color: colors.secondary }]}>Inspect recorded wealth and target weights. Select a strategy for the curve and allocations.</Text>
    <View style={styles.controls}>{strategies.map((name) => <Control key={name} label={`Inspect ${strategyName(name)}`} selected={strategy === name} onPress={() => setStrategy(name)} colors={colors} />)}</View>
    <Text accessibilityRole="header" style={[styles.heading, { color: colors.text }]}>Equity curve</Text>
    {equity.loading && <Text accessibilityLiveRegion="polite" style={[styles.body, { color: colors.secondary }]}>Loading equity curve…</Text>}
    {equity.error && <>
      <Text accessibilityRole="alert" style={[styles.body, { color: colors.error }]}>{`Equity unavailable. ${equity.error}`}</Text>
      <Control label="Retry equity" onPress={() => { void equity.reload(); }} colors={colors} />
    </>}
    {equity.data && <>
      <Text style={[styles.caption, { color: colors.secondary }]}>{equity.data.convention}</Text>
      <Curve wealth={equity.data.series.find((item) => item.strategy === strategy)!.wealth} name={strategyName(strategy)} colors={colors} />
      <Text style={[styles.caption, { color: colors.secondary }]}>{`${report.testDates[0]} → ${report.testDates[report.testDates.length - 1]} · ${report.costBps} ${report.costBps === 1 ? 'bp' : 'bps'}`}</Text>
    </>}
    <Text accessibilityLiveRegion="polite" style={[styles.date, { color: colors.text }]}>{`Date: ${report.testDates[dateIndex]} · ${dateIndex + 1} of ${report.testDates.length}`}</Text>
    <View style={styles.controls}>
      <Control label="Previous date" disabled={dateIndex === 0} onPress={() => setDateIndex((index) => index - 1)} colors={colors} />
      <Control label="Next date" disabled={dateIndex === report.testDates.length - 1} onPress={() => setDateIndex((index) => index + 1)} colors={colors} />
    </View>
    {equity.data && equity.data.series.map((item) => <Text key={item.strategy} style={[styles.value, { color: colors.text }]}>{`${strategyName(item.strategy)} wealth: ${item.wealth[dateIndex].toFixed(4)}`}</Text>)}
    <Text accessibilityRole="header" style={[styles.heading, { color: colors.text }]}>{`${strategyName(strategy)} allocations`}</Text>
    {allocations.loading && <Text accessibilityLiveRegion="polite" style={[styles.body, { color: colors.secondary }]}>Loading allocations…</Text>}
    {allocations.error && <>
      <Text accessibilityRole="alert" style={[styles.body, { color: colors.error }]}>{`Allocations unavailable. ${allocations.error}`}</Text>
      <Control label="Retry allocations" onPress={() => { void allocations.reload(); }} colors={colors} />
    </>}
    {allocations.data && <>
      <Text style={[styles.caption, { color: colors.secondary }]}>{allocations.data.convention}</Text>
      <Weights allocations={allocations.data} strategy={strategy} dateIndex={dateIndex} colors={colors} />
    </>}
  </View>;
}

const styles = StyleSheet.create({
  card: { borderWidth: StyleSheet.hairlineWidth, borderRadius: 24, padding: 22, marginBottom: 20 },
  kicker: { fontSize: 11, lineHeight: 17, fontWeight: '700', letterSpacing: 1.2, marginBottom: 8 },
  title: { fontSize: 25, lineHeight: 32, fontWeight: '700', letterSpacing: -0.5, marginBottom: 10 },
  heading: { fontSize: 20, lineHeight: 28, fontWeight: '600', marginTop: 24, marginBottom: 10 },
  body: { fontSize: 16, lineHeight: 24, marginBottom: 12 },
  caption: { fontSize: 14, lineHeight: 22, marginBottom: 8 },
  controls: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 12 },
  control: { minHeight: 48, flexShrink: 1, borderWidth: 1, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12, justifyContent: 'center' },
  controlText: { fontSize: 15, lineHeight: 22, fontWeight: '600' },
  date: { fontSize: 16, lineHeight: 24, fontWeight: '600', marginTop: 20, marginBottom: 12 },
  value: { fontSize: 16, lineHeight: 24, fontVariant: ['tabular-nums'], marginBottom: 8 },
  plot: { height: 160, marginHorizontal: 4, marginVertical: 8, borderBottomWidth: 1 },
  segment: { position: 'absolute', height: 2 },
  dot: { position: 'absolute', width: 6, height: 6, borderRadius: 3 },
  weight: { marginBottom: 16 },
  track: { height: 8, borderRadius: 4, overflow: 'hidden' },
  fill: { height: 8 },
});
