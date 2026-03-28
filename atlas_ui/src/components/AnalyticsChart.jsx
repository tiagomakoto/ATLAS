import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, LineElement, PointElement, Title, Tooltip, Legend, Filler } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, Title, Tooltip, Legend, Filler);

export default function AnalyticsChart({ data }) {
  if (!data || !data.walk_forward?.series) return null;

  const series = data.walk_forward.series;
  
  const chartData = {
    labels: series.map(s => s.window_end),
    datasets: [
      {
        label: 'IR Médio',
        data: series.map(s => s.ir_mean),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'Limite Inferior (95%)',
        data: series.map(s => s.ci_lower),
        borderColor: 'rgba(148, 163, 184, 0.5)',
        borderDash: [5, 5],
        pointRadius: 0,
        fill: false
      },
      {
        label: 'Limite Superior (95%)',
        data: series.map(s => s.ci_upper),
        borderColor: 'rgba(148, 163, 184, 0.5)',
        borderDash: [5, 5],
        pointRadius: 0,
        fill: '-1'
      }
    ]
  };

  const options = {
    responsive: true,
    plugins: {
      title: {
        display: true,
        text: 'Walk-Forward Analysis — IR por Janela',
        color: '#e2e8f0'
      },
      legend: {
        labels: { color: '#94a3b8' }
      }
    },
    scales: {
      x: {
        title: { display: true, text: 'Janela (meses)', color: '#94a3b8' },
        grid: { color: '#334155' },
        ticks: { color: '#94a3b8' }
      },
      y: {
        title: { display: true, text: 'Information Ratio', color: '#94a3b8' },
        grid: { color: '#334155' },
        ticks: { color: '#94a3b8' }
      }
    }
  };

  return <Line data={chartData} options={options} />;
}