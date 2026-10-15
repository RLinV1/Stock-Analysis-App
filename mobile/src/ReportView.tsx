import { StyleSheet, Text, View } from 'react-native';
import type { RunReport } from './api/contract';
import type { Colors } from './theme';
import { useReadableLayout } from './useReadableLayout';

const STRATEGY_NAMES: Record<string, string> = {
  lstm: 'LSTM',
  equal_weight: 'Equal weight',
  stock_bond_60_40: '60/40 stocks & bonds',
};

function percent(value: number, signed = false) {
  const rounded = value * 100;
  const prefix = signed && rounded > 0 ? '+' : '';
  return `${prefix}${rounded.toFixed(2)}%`;
}

function Metric({ label, value, colors, stacked }: { label: string; value: string; colors: Colors; stacked: boolean }) {
  return <View accessible accessibilityLabel={`${label}: ${value}`} style={[styles.metric, stacked && styles.stackedMetric]}>
    <Text style={[styles.metricLabel, { color: colors.secondary }]}>{label}</Text>
    <Text style={[styles.metricValue, { color: colors.text }]}>{value}</Text>
  </View>;
}

export function ReportView({ report, colors }: { report: RunReport; colors: Colors }) {
  const layout = useReadableLayout();
  const cardStyle = [styles.card, { backgroundColor: colors.surface, borderColor: colors.border, padding: layout.cardPadding, marginBottom: layout.gap }];
  const firstDate = report.testDates[0];
  const lastDate = report.testDates[report.testDates.length - 1];
  return <>
    <View style={cardStyle}>
      <Text style={[styles.kicker, { color: colors.accent }]}>SYNTHETIC DATA</Text>
      <Text accessibilityRole="header" style={[styles.title, { color: colors.text }]}>Measured report</Text>
      <Text style={[styles.body, { color: colors.secondary }]}>Compare the strategies evaluated in this run. These are synthetic results, not historical performance.</Text>
      <Text style={[styles.context, { color: colors.text }]}>{`Evaluation: ${firstDate} to ${lastDate}`}</Text>
      <Text style={[styles.context, { color: colors.secondary }]}>{`${report.testDates.length} observations · Transaction cost: ${report.costBps} ${report.costBps === 1 ? 'bp' : 'bps'}`}</Text>
      <Text style={[styles.context, { color: colors.secondary }]}>{`Method: ${report.methodLabel}`}</Text>
    </View>
    {Object.entries(report.strategies).map(([name, metrics]) => <View key={name} style={cardStyle}>
      <Text style={[styles.kicker, { color: colors.secondary }]}>{name === 'lstm' ? 'LEARNED STRATEGY' : 'BASELINE'}</Text>
      <Text accessibilityRole="header" style={[styles.strategy, { color: colors.text }]}>{STRATEGY_NAMES[name] ?? name}</Text>
      <Text style={[styles.returnLabel, { color: colors.secondary }]}>Cumulative return</Text>
      <Text accessibilityLabel={`Cumulative return: ${percent(metrics.cumulativeReturn, true)}`} style={[styles.returnValue, layout.stacked && styles.compactReturn, { color: colors.text }]}>{percent(metrics.cumulativeReturn, true)}</Text>
      <View style={[styles.metrics, layout.stacked && styles.stackedMetrics, { borderColor: colors.border, gap: layout.gap }]}>
        <Metric label="Sharpe ratio" value={metrics.sharpe === null ? 'Unavailable' : metrics.sharpe.toFixed(2)} colors={colors} stacked={layout.stacked} />
        <Metric label="Annualized volatility" value={percent(metrics.annualizedVolatility)} colors={colors} stacked={layout.stacked} />
        <Metric label="Maximum drawdown" value={percent(metrics.maxDrawdown)} colors={colors} stacked={layout.stacked} />
        <Metric label="Total turnover (L1)" value={metrics.totalTurnover.toFixed(2)} colors={colors} stacked={layout.stacked} />
        <Metric label="Summed cost / return units" value={metrics.totalCostReturnUnits.toFixed(6)} colors={colors} stacked={layout.stacked} />
        <Metric label="Observations" value={String(metrics.observations)} colors={colors} stacked={layout.stacked} />
      </View>
      {metrics.sharpeNote !== null && <Text style={[styles.note, { color: colors.secondary }]}>{`Sharpe: ${metrics.sharpeNote}`}</Text>}
    </View>)}
    <View style={cardStyle}>
      <Text accessibilityRole="header" style={[styles.strategy, { color: colors.text }]}>About this result</Text>
      <Text style={[styles.body, { color: colors.secondary }]}>All displayed strategies share the report&apos;s evaluation dates and transaction cost. No values are estimated by the app.</Text>
      <Text selectable style={[styles.context, { color: colors.secondary }]}>{`Research run: ${report.researchRunId}`}</Text>
    </View>
  </>;
}

const styles = StyleSheet.create({
  card: { borderWidth: StyleSheet.hairlineWidth, borderRadius: 24, padding: 22, marginBottom: 20 },
  kicker: { fontSize: 11, lineHeight: 17, fontWeight: '700', letterSpacing: 1.2, marginBottom: 8 },
  title: { fontSize: 27, lineHeight: 34, fontWeight: '700', letterSpacing: -0.6, marginBottom: 10 },
  strategy: { fontSize: 21, lineHeight: 28, fontWeight: '600', letterSpacing: -0.3 },
  body: { fontSize: 16, lineHeight: 24, marginBottom: 12 },
  context: { fontSize: 14, lineHeight: 22, marginTop: 4 },
  returnLabel: { fontSize: 14, lineHeight: 21, marginTop: 22 },
  returnValue: { fontSize: 38, lineHeight: 46, fontWeight: '600', letterSpacing: -1, fontVariant: ['tabular-nums'], marginBottom: 18 },
  compactReturn: { fontSize: 32, lineHeight: 40, letterSpacing: -0.6 },
  metrics: { flexDirection: 'row', flexWrap: 'wrap', borderTopWidth: StyleSheet.hairlineWidth, paddingTop: 18, gap: 20 },
  metric: { flexGrow: 1, flexBasis: 140, minWidth: 0 },
  stackedMetric: { flexGrow: 0, flexBasis: 'auto' },
  stackedMetrics: { flexDirection: 'column' },
  metricLabel: { fontSize: 13, lineHeight: 20 },
  metricValue: { fontSize: 19, lineHeight: 27, fontWeight: '600', fontVariant: ['tabular-nums'], marginTop: 3 },
  note: { fontSize: 14, lineHeight: 22, marginTop: 16 },
});
