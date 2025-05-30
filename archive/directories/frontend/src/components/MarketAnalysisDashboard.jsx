import React, { useState, useEffect, useMemo } from 'react';
import AdaptiveChart from './AdaptiveChart';
import { TrendValue, TrendBadge, TrendCard } from './TrendAwareElements';
import { useDataTrendColors, useValueComparisonColors } from '../hooks/useAdaptiveColor';

// Sample data fetching function (would be replaced with actual API calls)
const fetchMarketAnalysisData = async (countyId, period) => {
  // Simulate API call delay
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // Return structured data that would come from the real API
  return {
    summary: {
      averagePrice: 450000 + (Math.random() * 50000),
      medianPrice: 425000 + (Math.random() * 40000),
      salesVolume: 1250 + (Math.random() * 200),
      averageDaysOnMarket: 45 + (Math.random() * 15),
      pricePerSqFt: 350 + (Math.random() * 20)
    },
    previousPeriod: {
      averagePrice: 440000,
      medianPrice: 415000,
      salesVolume: 1200,
      averageDaysOnMarket: 50,
      pricePerSqFt: 340
    },
    trendData: {
      prices: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        averagePrices: [440000, 442000, 445000, 450000, 455000, 460000],
        medianPrices: [415000, 418000, 420000, 422000, 425000, 430000]
      },
      salesVolume: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        data: [1200, 1180, 1220, 1240, 1250, 1280]
      },
      daysOnMarket: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        data: [50, 48, 46, 45, 43, 42]
      },
      pricePerSqFt: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        data: [340, 342, 345, 348, 350, 355]
      }
    }
  };
};

/**
 * Market Analysis Dashboard component that demonstrates adaptive color scheme
 * based on data trends
 */
const MarketAnalysisDashboard = ({ countyId = 'SAMPLE_COUNTY' }) => {
  const [data, setData] = useState(null);
  const [previousData, setPreviousData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('6M'); // 6 months
  
  // Fetch data when county or period changes
  useEffect(() => {
    const getData = async () => {
      setLoading(true);
      try {
        const result = await fetchMarketAnalysisData(countyId, period);
        setPreviousData(data); // Store previous data for comparison
        setData(result);
      } catch (error) {
        console.error('Error fetching market analysis data:', error);
      } finally {
        setLoading(false);
      }
    };
    
    getData();
  }, [countyId, period]);
  
  // Price trend colors using our custom hook
  const priceTrendColors = useDataTrendColors(
    data?.trendData?.prices?.averagePrices, 
    { positiveIsGood: true, threshold: 3 }
  );
  
  // Days on market trend colors (lower is better, so positiveIsGood is false)
  const daysOnMarketColors = useDataTrendColors(
    data?.trendData?.daysOnMarket?.data,
    { positiveIsGood: false, threshold: 3 }
  );
  
  // Sales volume comparison colors
  const salesVolumeComparison = useValueComparisonColors(
    data?.summary?.salesVolume,
    data?.previousPeriod?.salesVolume,
    { positiveIsGood: true, threshold: 3 }
  );
  
  // KPI cards data with trend indicators
  const kpiCards = useMemo(() => {
    if (!data) return [];
    
    return [
      {
        title: 'Average Price',
        value: data.summary.averagePrice,
        previousValue: data.previousPeriod.averagePrice,
        formatter: (val) => `$${Math.round(val).toLocaleString()}`,
        positiveIsGood: true,
        icon: 'home'
      },
      {
        title: 'Median Price',
        value: data.summary.medianPrice,
        previousValue: data.previousPeriod.medianPrice,
        formatter: (val) => `$${Math.round(val).toLocaleString()}`,
        positiveIsGood: true,
        icon: 'tags'
      },
      {
        title: 'Sales Volume',
        value: data.summary.salesVolume,
        previousValue: data.previousPeriod.salesVolume,
        formatter: (val) => Math.round(val).toLocaleString(),
        positiveIsGood: true,
        icon: 'bar-chart-line'
      },
      {
        title: 'Avg. Days on Market',
        value: data.summary.averageDaysOnMarket,
        previousValue: data.previousPeriod.averageDaysOnMarket,
        formatter: (val) => `${Math.round(val)} days`,
        positiveIsGood: false, // Lower is better
        icon: 'clock'
      }
    ];
  }, [data]);
  
  if (loading && !data) {
    return (
      <div className="loading-container text-center py-5">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="mt-3">Loading market analysis data...</p>
      </div>
    );
  }
  
  if (!data) {
    return (
      <div className="alert alert-warning">
        No market analysis data available for this county.
      </div>
    );
  }
  
  return (
    <div className="market-analysis-dashboard">
      <div className="dashboard-header d-flex justify-content-between align-items-center mb-4">
        <h2>Market Analysis Dashboard</h2>
        <div className="period-selector btn-group">
          <button 
            className={`btn btn-sm ${period === '3M' ? 'btn-primary' : 'btn-outline-primary'}`}
            onClick={() => setPeriod('3M')}
          >
            3 Months
          </button>
          <button 
            className={`btn btn-sm ${period === '6M' ? 'btn-primary' : 'btn-outline-primary'}`}
            onClick={() => setPeriod('6M')}
          >
            6 Months
          </button>
          <button 
            className={`btn btn-sm ${period === '1Y' ? 'btn-primary' : 'btn-outline-primary'}`}
            onClick={() => setPeriod('1Y')}
          >
            1 Year
          </button>
        </div>
      </div>
      
      {/* KPI Cards with Trend-Aware Elements */}
      <div className="row mb-4">
        {kpiCards.map((card, index) => {
          const comparison = useValueComparisonColors(
            card.value, 
            card.previousValue,
            { positiveIsGood: card.positiveIsGood, threshold: 3 }
          );
          
          return (
            <div className="col-md-3" key={index}>
              <TrendCard 
                trendValue={comparison.trendPercentage}
                positiveIsGood={card.positiveIsGood}
                className="h-100"
              >
                <div className="card-body">
                  <h5 className="card-title d-flex align-items-center">
                    <i className={`bi bi-${card.icon} me-2`}></i>
                    {card.title}
                  </h5>
                  <div className="d-flex justify-content-between align-items-baseline">
                    <TrendValue
                      value={card.value}
                      previousValue={card.previousValue}
                      positiveIsGood={card.positiveIsGood}
                      className="fs-4 fw-bold"
                      formatter={card.formatter}
                    />
                    <TrendBadge
                      trendValue={comparison.trendPercentage}
                      positiveIsGood={card.positiveIsGood}
                    >
                      {Math.abs(comparison.trendPercentage).toFixed(1)}%
                    </TrendBadge>
                  </div>
                  <div className="text-muted small">
                    vs. previous period: {card.formatter(card.previousValue)}
                  </div>
                </div>
              </TrendCard>
            </div>
          );
        })}
      </div>
      
      {/* Chart Section with Adaptive Colors */}
      <div className="row mb-4">
        <div className="col-md-6">
          <div className="card h-100">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Price Trends</h5>
              <TrendBadge
                trendValue={priceTrendColors.trendPercentage}
                positiveIsGood={true}
              >
                {priceTrendColors.trendDirection === 'positive' ? 'Rising' : 
                 priceTrendColors.trendDirection === 'negative' ? 'Falling' : 'Stable'}
              </TrendBadge>
            </div>
            <div className="card-body">
              <AdaptiveChart
                type="line"
                labels={data.trendData.prices.labels}
                datasets={[
                  {
                    label: 'Average Price',
                    data: data.trendData.prices.averagePrices,
                    tension: 0.4,
                    fill: true,
                  },
                  {
                    label: 'Median Price',
                    data: data.trendData.prices.medianPrices,
                    tension: 0.4,
                    borderDash: [5, 5],
                  }
                ]}
                trendConfig={{ positiveIsGood: true, threshold: 3 }}
              />
            </div>
          </div>
        </div>
        
        <div className="col-md-6">
          <div className="card h-100">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Days on Market</h5>
              <TrendBadge
                trendValue={daysOnMarketColors.trendPercentage}
                positiveIsGood={false} // Lower is better
              >
                {daysOnMarketColors.trendDirection === 'positive' ? 'Improving' : 
                 daysOnMarketColors.trendDirection === 'negative' ? 'Slowing' : 'Stable'}
              </TrendBadge>
            </div>
            <div className="card-body">
              <AdaptiveChart
                type="line"
                labels={data.trendData.daysOnMarket.labels}
                datasets={[
                  {
                    label: 'Avg. Days on Market',
                    data: data.trendData.daysOnMarket.data,
                    tension: 0.4,
                    fill: true,
                  }
                ]}
                trendConfig={{ positiveIsGood: false, threshold: 3 }}
              />
            </div>
          </div>
        </div>
      </div>
      
      <div className="row">
        <div className="col-md-6">
          <div className="card h-100">
            <div className="card-header">
              <h5 className="mb-0">Sales Volume</h5>
            </div>
            <div className="card-body">
              <AdaptiveChart
                type="bar"
                labels={data.trendData.salesVolume.labels}
                datasets={[
                  {
                    label: 'Sales Volume',
                    data: data.trendData.salesVolume.data,
                    fill: true,
                  }
                ]}
                trendConfig={{ positiveIsGood: true, threshold: 3 }}
              />
            </div>
          </div>
        </div>
        
        <div className="col-md-6">
          <div className="card h-100">
            <div className="card-header">
              <h5 className="mb-0">Price per Sq. Ft.</h5>
            </div>
            <div className="card-body">
              <AdaptiveChart
                type="line"
                labels={data.trendData.pricePerSqFt.labels}
                datasets={[
                  {
                    label: 'Price per Sq. Ft.',
                    data: data.trendData.pricePerSqFt.data,
                    tension: 0.4,
                    fill: true,
                  }
                ]}
                trendConfig={{ positiveIsGood: true, threshold: 3 }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketAnalysisDashboard;