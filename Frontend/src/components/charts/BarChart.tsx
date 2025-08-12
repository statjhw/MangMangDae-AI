import { motion } from 'framer-motion';
import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { CHART_COLORS } from '../../utils/constants';

interface BarChartData {
  name: string;
  value: number;
  color?: string;
}

interface BarChartProps {
  data: BarChartData[];
  title?: string;
  xAxisLabel?: string;
  yAxisLabel?: string;
  height?: number;
  className?: string;
}

const BarChart = ({ 
  data, 
  title, 
  xAxisLabel, 
  yAxisLabel, 
  height = 300,
  className 
}: BarChartProps) => {
  const chartData = data.map((item, index) => ({
    ...item,
    color: item.color || CHART_COLORS[index % CHART_COLORS.length],
  }));

  return (
    <motion.div
      className={`bg-white rounded-xl p-6 shadow-lg ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      {title && (
        <h3 className="text-lg font-semibold text-secondary-800 mb-4">{title}</h3>
      )}
      
      <ResponsiveContainer width="100%" height={height}>
        <RechartsBarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="name" 
            tick={{ fontSize: 12, fill: '#64748b' }}
            axisLine={{ stroke: '#e2e8f0' }}
            tickLine={{ stroke: '#e2e8f0' }}
          />
          <YAxis 
            tick={{ fontSize: 12, fill: '#64748b' }}
            axisLine={{ stroke: '#e2e8f0' }}
            tickLine={{ stroke: '#e2e8f0' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
            labelStyle={{ color: '#374151', fontWeight: '600' }}
          />
          <Bar 
            dataKey="value" 
            fill="#3B82F6"
            radius={[4, 4, 0, 0]}
            animationDuration={1000}
            animationBegin={200}
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color}
              />
            ))}
          </Bar>
        </RechartsBarChart>
      </ResponsiveContainer>
      
      {(xAxisLabel || yAxisLabel) && (
        <div className="flex justify-between text-xs text-secondary-500 mt-2">
          {xAxisLabel && <span>{xAxisLabel}</span>}
          {yAxisLabel && <span>{yAxisLabel}</span>}
        </div>
      )}
    </motion.div>
  );
};

export default BarChart; 