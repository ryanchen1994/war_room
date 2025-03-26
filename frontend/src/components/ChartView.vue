<template>
  <div class="chart-view">
    <h2 class="dashboard-title">工程績效指標</h2>
    
    <div class="kpi-cards">
      <div class="kpi-card">
        <div class="kpi-icon">⏱️</div>
        <div class="kpi-content">
          <div class="kpi-value">{{ kpiData.onTimeProjects }}%</div>
          <div class="kpi-label">準時完工率</div>
        </div>
      </div>
      
      <div class="kpi-card">
        <div class="kpi-icon">💰</div>
        <div class="kpi-content">
          <div class="kpi-value">{{ kpiData.budgetCompliance }}%</div>
          <div class="kpi-label">預算達成率</div>
        </div>
      </div>
      
      <div class="kpi-card">
        <div class="kpi-icon">🔍</div>
        <div class="kpi-content">
          <div class="kpi-value">{{ kpiData.qualityScore }}</div>
          <div class="kpi-label">品質評分</div>
        </div>
      </div>
      
      <div class="kpi-card">
        <div class="kpi-icon">🏗️</div>
        <div class="kpi-content">
          <div class="kpi-value">{{ kpiData.activeProjects }}</div>
          <div class="kpi-label">進行中專案</div>
        </div>
      </div>
    </div>
    
    <div class="chart-container">
      <canvas ref="performanceCanvas"></canvas>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Chart } from 'chart.js/auto'
import axios from 'axios'

export default {
  name: 'ChartView',
  setup() {
    const performanceCanvas = ref(null)
    const chart = ref(null)
    const resizeObserver = ref(null)
    const chartInitialized = ref(false)
    const kpiData = ref({
      onTimeProjects: 85,
      budgetCompliance: 92,
      qualityScore: 4.7,
      activeProjects: 12
    })
    
    // 模擬資料 - 實際應用中應從API獲取
    const monthlyData = ref([
      { month: '一月', completed: 2, delayed: 1, budget: 85 },
      { month: '二月', completed: 3, delayed: 0, budget: 95 },
      { month: '三月', completed: 1, delayed: 1, budget: 90 },
      { month: '四月', completed: 4, delayed: 1, budget: 88 },
      { month: '五月', completed: 2, delayed: 0, budget: 92 },
      { month: '六月', completed: 3, delayed: 2, budget: 85 }
    ])
    
    // 創建或更新圖表
    const createChart = () => {
      // 確保 canvas 元素存在且可見
      if (!performanceCanvas.value || performanceCanvas.value.offsetParent === null) {
        console.warn('圖表 Canvas 元素不可見，延遲創建')
        setTimeout(createChart, 500)
        return
      }
      
      // 設置 Canvas 尺寸
      if (performanceCanvas.value && performanceCanvas.value.parentElement) {
        // 先設置樣式尺寸 - 確保 canvas 填滿容器但不溢出
        performanceCanvas.value.style.width = '100%'
        performanceCanvas.value.style.height = '100%'
        
        // 獲取容器尺寸
        const parentWidth = performanceCanvas.value.parentElement.clientWidth
        // 如果父元素高度為0，使用一個合理的最小高度，但確保它不會太大
        const parentHeight = performanceCanvas.value.parentElement.clientHeight || Math.min(window.innerHeight * 0.3, 300)
        
        // 設置實際像素尺寸 - 考慮設備像素比以確保清晰度
        const dpr = window.devicePixelRatio || 1
        performanceCanvas.value.width = parentWidth * dpr
        performanceCanvas.value.height = parentHeight * dpr
        
        // 調整繪圖上下文以匹配設備像素比
        const ctx = performanceCanvas.value.getContext('2d')
        if (ctx) {
          ctx.scale(dpr, dpr)
        }
      }
      
      // 如果已存在圖表，先銷毀它
      if (chart.value) {
        chart.value.destroy();
        chart.value = null;
      }
      
      // 等待下一個渲染週期，確保 canvas 已經渲染
      nextTick(() => {
        const ctx = performanceCanvas.value.getContext('2d')
        
        // 確保 canvas 上下文存在
        if (!ctx) {
          console.error('無法獲取 canvas 上下文');
          return;
        }
        
        // 創建新圖表
        chart.value = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: monthlyData.value.map(item => item.month),
            datasets: [
              {
                label: '按時完成專案',
                data: monthlyData.value.map(item => item.completed),
                backgroundColor: 'rgba(46, 204, 113, 0.7)',
                borderColor: 'rgba(46, 204, 113, 1)',
                borderWidth: 1,
                borderRadius: 4,
                barPercentage: 0.6
              },
              {
                label: '延遲專案',
                data: monthlyData.value.map(item => item.delayed),
                backgroundColor: 'rgba(231, 76, 60, 0.7)',
                borderColor: 'rgba(231, 76, 60, 1)',
                borderWidth: 1,
                borderRadius: 4,
                barPercentage: 0.6
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
              duration: 1000, // 控制動畫時長
              easing: 'easeOutQuad'
            },
            plugins: {
              title: {
                display: true,
                text: '月度專案完成情況',
                font: {
                  size: 16,
                  weight: 'bold'
                }
              },
              legend: {
                position: 'bottom'
              },
              tooltip: {
                mode: 'index',
                intersect: false
              }
            },
            scales: {
              x: {
                grid: {
                  display: false
                }
              },
              y: {
                beginAtZero: true,
                ticks: {
                  precision: 0
                }
              }
            }
          }
        });
        
        chartInitialized.value = true;
      });
    }
    
    // 處理視窗大小變化
    let resizeTimeout = null;
    const handleResize = () => {
      if (!chartInitialized.value) return;
      
      // 清除之前的計時器，實現防抖
      if (resizeTimeout) {
        clearTimeout(resizeTimeout);
      }
      
      // 使用 setTimeout 延遲執行，避免頻繁更新
      resizeTimeout = setTimeout(() => {
        // 重新創建圖表
        createChart();
        resizeTimeout = null;
      }, 300);
    }
    
    // 從API獲取資料
    const fetchData = async () => {
      try {
        console.log('開始獲取績效數據...');
        // 嘗試從 API 獲取數據
        const response = await axios.get('http://localhost:5000/api/performance');
        console.log('獲取到的績效數據:', response.data);
        
        if (response.data && response.data.kpi) {
          kpiData.value = response.data.kpi;
        }
        
        if (response.data && response.data.monthly) {
          monthlyData.value = response.data.monthly;
        }
      } catch (error) {
        console.error('獲取績效資料失敗:', error);
        // 發生錯誤時使用模擬資料
        console.log('使用模擬數據創建圖表');
        
        // 使用已有的模擬數據
        kpiData.value = {
          onTimeProjects: 85,
          budgetCompliance: 92,
          qualityScore: 4.7,
          activeProjects: 12
        };
        
        monthlyData.value = [
          { month: '一月', completed: 2, delayed: 1, budget: 85 },
          { month: '二月', completed: 3, delayed: 0, budget: 95 },
          { month: '三月', completed: 1, delayed: 1, budget: 90 },
          { month: '四月', completed: 4, delayed: 1, budget: 88 },
          { month: '五月', completed: 2, delayed: 0, budget: 92 },
          { month: '六月', completed: 3, delayed: 2, budget: 85 }
        ];
      } finally {
        // 無論成功或失敗，都確保圖表被創建
        // 等待DOM更新完成
        nextTick(() => {
          // 給足夠的時間讓容器準備好
          setTimeout(() => {
            // 檢查容器是否已經可見
            if (performanceCanvas.value && performanceCanvas.value.parentElement) {
              createChart();
            } else {
              // 如果容器還不可見，再多等一會
              console.log('圖表容器尚未準備好，再等待...');
              setTimeout(createChart, 500);
            }
          }, 300);
        });
      }
    }
    
    onMounted(() => {
      // 等待 DOM 完全渲染後再初始化
      nextTick(() => {
        // 先獲取數據
        fetchData();
        
        // 使用 ResizeObserver 監聽容器大小變化
        if (window.ResizeObserver) {
          resizeObserver.value = new ResizeObserver(() => {
            if (chartInitialized.value) {
              handleResize();
            }
          });
          
          // 確保容器存在後再設置觀察者
          const setupObserver = () => {
            if (performanceCanvas.value && performanceCanvas.value.parentElement) {
              resizeObserver.value.observe(performanceCanvas.value.parentElement);
            } else {
              // 如果容器還不存在，稍後再試
              setTimeout(setupObserver, 200);
            }
          };
          
          setupObserver();
        }
        
        // 同時也監聽視窗大小變化
        window.addEventListener('resize', handleResize);
      });
    });
    
    onBeforeUnmount(() => {
      // 清理資源
      if (chart.value) {
        chart.value.destroy();
        chart.value = null;
      }
      
      // 停止觀察大小變化
      if (resizeObserver.value) {
        resizeObserver.value.disconnect();
      }
      
      // 移除事件監聽器
      window.removeEventListener('resize', handleResize);
    });
    
    return {
      performanceCanvas,
      kpiData
    }
  }
}
</script>

<style scoped>
.chart-view {
  background-color: #ffffff;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  padding: 20px;
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.dashboard-title {
  color: #2c3e50;
  font-size: 1.5rem;
  margin-bottom: 20px;
  text-align: left;
  border-bottom: 2px solid #f0f0f0;
  padding-bottom: 10px;
  flex-shrink: 0;
}

.kpi-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.kpi-card {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  display: flex;
  align-items: center;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.kpi-icon {
  font-size: 1.5rem;
  margin-right: 12px;
  opacity: 0.8;
}

.kpi-content {
  flex: 1;
}

.kpi-value {
  font-size: 1.4rem;
  font-weight: bold;
  color: #2c3e50;
}

.kpi-label {
  font-size: 0.9rem;
  color: #7f8c8d;
  margin-top: 4px;
}

.chart-container {
  position: relative;
  width: 100%;
  flex-grow: 1;
  min-height: 250px;
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  box-sizing: border-box;
  overflow: hidden; /* 防止內容溢出 */
}

canvas {
  max-width: 100%;
  max-height: 100%;
  display: block; /* 消除底部間隙 */
}

/* 小螢幕適配 */
@media (max-width: 767px) {
  .kpi-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .chart-container {
    min-height: 200px; /* 小螢幕上減少最小高度 */
  }
}

@media (max-width: 480px) {
  .kpi-cards {
    grid-template-columns: 1fr;
    gap: 10px;
  }
}
</style>