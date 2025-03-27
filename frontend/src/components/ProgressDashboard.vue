<template>
  <div class="progress-dashboard">
    <h2 class="dashboard-title">工程進度總覽</h2>
    
    <!-- 進度概況卡片 -->
    <div class="progress-summary">
      <div class="summary-card">
        <div class="card-title">專案總數</div>
        <div class="card-value">{{ progressData.length }}</div>
      </div>
      <div class="summary-card">
        <div class="card-title">平均進度</div>
        <div class="card-value">{{ averageProgress }}%</div>
      </div>
      <div class="summary-card">
        <div class="card-title">超前專案</div>
        <div class="card-value">{{ aheadProjects }}</div>
      </div>
      <div class="summary-card">
        <div class="card-title">落後專案</div>
        <div class="card-value">{{ behindProjects }}</div>
      </div>
    </div>
    
    <!-- 專案圖表區域 - 每個專案一個圖表 -->
    <div class="projects-charts-container">
      <div v-for="(project, index) in progressData" :key="project.PROJM_NO" class="project-chart-card">
        <h3 class="project-chart-title">{{ project.PROJM_NAME || '未命名專案' }}</h3>
        <div class="project-chart-info">
          <span class="project-id">專案編號: {{ project.PROJM_NO }}</span>
          <span :class="getStatusClass(project)" class="project-status">{{ getStatusText(project) }}</span>
        </div>
        <div class="project-chart-container">
          <canvas :ref="el => { if (el) projectCharts[index] = el }"></canvas>
        </div>
        <div class="project-chart-details">
          <div class="detail-item">
            <span class="detail-label">預計工作天數:</span>
            <span class="detail-value">{{ project.PWORK_DAY || 0 }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">實際工作天數:</span>
            <span class="detail-value">{{ project.AWORK_DAY || 0 }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">預計進度:</span>
            <span class="detail-value">{{ parseFloat(project.PPER || 0).toFixed(3) }}%</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">實際進度:</span>
            <span class="detail-value">{{ parseFloat(project.APER || 0).toFixed(3) }}%</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">更新日期:</span>
            <span class="detail-value">{{ formatDate(project.DAY_DATE) }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <p v-if="socketMessage" class="realtime-message">
      <span class="message-icon">📣</span> {{ socketMessage }}
    </p>
  </div>
</template>

<script>
import axios from 'axios'
import { io } from 'socket.io-client'
import { Chart } from 'chart.js/auto'
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'

export default {
  name: 'ProgressDashboard',
  setup() {
    const progressData = ref([])
    const socketMessage = ref('')
    const projectCharts = ref([])
    let intervalId = null
    let socket = null
    let charts = []

    // 計算平均進度
    const averageProgress = computed(() => {
      if (progressData.value.length === 0) return 0;
      const sum = progressData.value.reduce((acc, project) => acc + (project.APER || 0), 0);
      return Math.round(sum / progressData.value.length);
    });

    // 計算超前專案數量
    const aheadProjects = computed(() => {
      return progressData.value.filter(project => 
        (project.APER || 0) > (project.PPER || 0)
      ).length;
    });

    // 計算落後專案數量
    const behindProjects = computed(() => {
      return progressData.value.filter(project => 
        (project.APER || 0) < (project.PPER || 0)
      ).length;
    });

    const formatDate = (dateString) => {
      if (!dateString) return '未設定';
      try {
        // 處理格式為 YYYYMMDD 的日期字符串
        if (typeof dateString === 'string' && dateString.length === 8 && !dateString.includes('-')) {
          const year = dateString.substring(0, 4);
          const month = dateString.substring(4, 6);
          const day = dateString.substring(6, 8);
          return `${year}-${month}-${day}`;
        }
        
        // 處理標準日期格式
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return '日期格式錯誤';
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
      } catch (e) {
        console.error('日期格式化錯誤:', e);
        return '日期錯誤';
      }
    }

    // 獲取專案狀態文字
    const getStatusText = (project) => {
      if (!project.PPER || !project.APER) return '未開始';
      
      if (project.BUILD_REM202 && project.BUILD_REM202.includes('超前')) {
        return '超前';
      } else if (project.BUILD_REM202 && project.BUILD_REM202.includes('落後')) {
        return '落後';
      } else if (project.APER >= 100) {
        return '已完成';
      } else if (project.APER >= project.PPER) {
        return '符合進度';
      } else {
        return '落後';
      }
    }

    // 獲取專案狀態樣式類別
    const getStatusClass = (project) => {
      const status = getStatusText(project);
      if (status === '超前') return 'status-ahead';
      if (status === '落後') return 'status-behind';
      if (status === '已完成') return 'status-completed';
      if (status === '符合進度') return 'status-ontrack';
      return '';
    }

    // 更新所有專案圖表
    const updateProjectCharts = () => {
      // 先清除舊的圖表
      charts.forEach(chart => {
        if (chart) {
          try {
            chart.destroy();
          } catch (e) {
            console.warn('銷毀圖表時出錯:', e);
          }
        }
      });
      charts = [];

      // 為每個專案創建新圖表
      projectCharts.value.forEach((canvas, index) => {
        if (!canvas) return;
        
        const project = progressData.value[index];
        if (!project) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // 設置 Canvas 尺寸
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;

        // 獲取狀態顏色
        const statusColor = getStatusColor(project);

        // 創建圖表
        const chart = new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels: ['實際進度', '預計進度', '剩餘'],
            datasets: [
              {
                data: [
                  project.APER || 0, 
                  (project.PPER > project.APER) ? (project.PPER - project.APER) : 0, 
                  100 - Math.max(project.PPER || 0, project.APER || 0)
                ],
                backgroundColor: [
                  statusColor.bg,
                  'rgba(54, 162, 235, 0.5)',
                  'rgba(220, 220, 220, 0.3)'
                ],
                borderColor: [
                  statusColor.border,
                  'rgba(54, 162, 235, 1)',
                  'rgba(220, 220, 220, 0.5)'
                ],
                borderWidth: 1
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
              legend: {
                position: 'bottom',
                labels: {
                  padding: 10
                }
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    const label = context.label || '';
                    const value = parseFloat(context.raw).toFixed(3);
                    
                    if (label === '實際進度') {
                      return `實際進度: ${value}%`;
                    } else if (label === '預計進度') {
                      return `預計進度差異: +${value}%`;
                    } else {
                      return `剩餘: ${value}%`;
                    }
                  },
                  afterLabel: function(context) {
                    if (context.label === '實際進度') {
                      return `總預計進度: ${parseFloat(project.PPER || 0).toFixed(3)}%`;
                    }
                    return null;
                  }
                }
              },
              // 添加中心文字顯示
              doughnutLabel: {
                beforeDatasetsDraw(chart) {
                  const { ctx, data } = chart;
                  ctx.save();
                  const xCoor = chart.getDatasetMeta(0).data[0].x;
                  const yCoor = chart.getDatasetMeta(0).data[0].y;
                  ctx.font = 'bold 16px Arial';
                  ctx.fillStyle = '#333';
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  
                  const actualProgress = parseFloat(project.APER || 0).toFixed(1);
                  const plannedProgress = parseFloat(project.PPER || 0).toFixed(1);
                  
                  ctx.fillText(`${actualProgress}%`, xCoor, yCoor - 10);
                  
                  ctx.font = '12px Arial';
                  ctx.fillStyle = '#666';
                  ctx.fillText(`計劃: ${plannedProgress}%`, xCoor, yCoor + 15);
                  
                  ctx.restore();
                }
              }
            }
          },
          plugins: [{
            id: 'doughnutLabel',
            beforeDatasetsDraw(chart) {
              const { ctx, data } = chart;
              ctx.save();
              
              if (chart.getDatasetMeta(0).data[0]) {
                const xCoor = chart.getDatasetMeta(0).data[0].x;
                const yCoor = chart.getDatasetMeta(0).data[0].y;
                
                ctx.font = 'bold 16px Arial';
                ctx.fillStyle = '#333';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                
                const actualProgress = parseFloat(project.APER || 0).toFixed(1);
                const plannedProgress = parseFloat(project.PPER || 0).toFixed(1);
                
                ctx.fillText(`${actualProgress}%`, xCoor, yCoor - 10);
                
                ctx.font = '12px Arial';
                ctx.fillStyle = '#666';
                ctx.fillText(`計劃: ${plannedProgress}%`, xCoor, yCoor + 15);
              }
              
              ctx.restore();
            }
          }]
        });

        charts.push(chart);
      });
    };

    // 獲取狀態對應的顏色
    const getStatusColor = (project) => {
      const status = getStatusText(project);
      if (status === '超前') {
        return {
          bg: 'rgba(75, 192, 192, 0.5)',
          border: 'rgba(75, 192, 192, 1)'
        };
      } else if (status === '落後') {
        return {
          bg: 'rgba(255, 99, 132, 0.5)',
          border: 'rgba(255, 99, 132, 1)'
        };
      } else if (status === '已完成') {
        return {
          bg: 'rgba(54, 162, 235, 0.5)',
          border: 'rgba(54, 162, 235, 1)'
        };
      } else {
        return {
          bg: 'rgba(255, 205, 86, 0.5)',
          border: 'rgba(255, 205, 86, 1)'
        };
      }
    };

    const fetchProgress = async () => {
      try {
        console.log('開始獲取進度數據...');
        const response = await axios.get('http://localhost:5000/api/remar-data');
        
        if (Array.isArray(response.data)) {
          progressData.value = response.data.map(project => {
            // 確保數值型別正確
            project.PWORK_DAY = parseInt(project.PWORK_DAY) || 0;
            project.AWORK_DAY = parseInt(project.AWORK_DAY) || 0;
            project.PPER = parseFloat(parseFloat(project.PPER).toFixed(3)) || 0; // 限制小數點後3位
            project.APER = parseFloat(parseFloat(project.APER).toFixed(3)) || 0; // 限制小數點後3位
            project.PMDAY = parseInt(project.PMDAY) || 0;
            project.YPPER = parseFloat(parseFloat(project.YPPER).toFixed(3)) || 0; // 限制小數點後3位
            
            return project;
          });
          
          // 延遲更新圖表，確保 DOM 已更新
          setTimeout(() => {
            updateProjectCharts();
          }, 100);
        } else {
          console.error('API 返回的數據不是數組格式:', response.data);
          // 使用模擬數據
          progressData.value = generateMockData();
          setTimeout(() => {
            updateProjectCharts();
          }, 100);
        }
      } catch (error) {
        console.error('獲取進度數據失敗:', error);
        // 使用模擬數據
        progressData.value = generateMockData();
        setTimeout(() => {
          updateProjectCharts();
        }, 100);
      }
    }

    // 生成模擬數據函數
    const generateMockData = () => {
      const today = new Date();
      return [
        {
          PROJM_NO: '0027-1',
          PROJM_NAME: '台北商辦大樓',
          BUILD_REM202: '超前5天',
          PST: new Date(today.getFullYear(), today.getMonth() - 2, 15).toISOString().split('T')[0],
          PFI: new Date(today.getFullYear(), today.getMonth() + 4, 20).toISOString().split('T')[0],
          AST: new Date(today.getFullYear(), today.getMonth() - 2, 10).toISOString().split('T')[0],
          AFI: null,
          PWORK_DAY: 180,
          AWORK_DAY: 60,
          PPER: 35,
          APER: 40,
          PMDAY: 5,
          REMARK_601: '工程進度超前，地下室結構已完成',
          YPPER: 40,
          DAY_DATE: new Date().toISOString().split('T')[0]
        },
        {
          PROJM_NO: '0040',
          PROJM_NAME: '新竹科技園區',
          BUILD_REM202: '落後3天',
          PST: new Date(today.getFullYear(), today.getMonth() - 3, 10).toISOString().split('T')[0],
          PFI: new Date(today.getFullYear(), today.getMonth() + 3, 15).toISOString().split('T')[0],
          AST: new Date(today.getFullYear(), today.getMonth() - 3, 15).toISOString().split('T')[0],
          AFI: null,
          PWORK_DAY: 180,
          AWORK_DAY: 90,
          PPER: 55,
          APER: 52,
          PMDAY: -3,
          REMARK_601: '因雨延誤部分工程，正在趕工中',
          YPPER: 52,
          DAY_DATE: new Date().toISOString().split('T')[0]
        },
        {
          PROJM_NO: '0051',
          PROJM_NAME: '台中住宅社區',
          BUILD_REM202: '已完工',
          PST: new Date(today.getFullYear(), today.getMonth() - 5, 5).toISOString().split('T')[0],
          PFI: new Date(today.getFullYear(), today.getMonth() - 1, 10).toISOString().split('T')[0],
          AST: new Date(today.getFullYear(), today.getMonth() - 5, 8).toISOString().split('T')[0],
          AFI: new Date(today.getFullYear(), today.getMonth() - 1, 5).toISOString().split('T')[0],
          PWORK_DAY: 120,
          AWORK_DAY: 120,
          PPER: 100,
          APER: 100,
          PMDAY: 0,
          REMARK_601: '工程已完成，準備驗收',
          YPPER: 100,
          DAY_DATE: new Date().toISOString().split('T')[0]
        },
        {
          PROJM_NO: '0021',
          PROJM_NAME: '高雄港口擴建',
          BUILD_REM202: '符合進度',
          PST: new Date(today.getFullYear(), today.getMonth() - 1, 15).toISOString().split('T')[0],
          PFI: new Date(today.getFullYear(), today.getMonth() + 5, 20).toISOString().split('T')[0],
          AST: new Date(today.getFullYear(), today.getMonth() - 1, 15).toISOString().split('T')[0],
          AFI: null,
          PWORK_DAY: 180,
          AWORK_DAY: 45,
          PPER: 25,
          APER: 25,
          PMDAY: 0,
          REMARK_601: '工程進度符合預期',
          YPPER: 25,
          DAY_DATE: new Date().toISOString().split('T')[0]
        },
        {
          PROJM_NO: '0038',
          PROJM_NAME: '花蓮觀光飯店',
          BUILD_REM202: '未開始',
          PST: new Date(today.getFullYear(), today.getMonth() + 1, 5).toISOString().split('T')[0],
          PFI: new Date(today.getFullYear(), today.getMonth() + 7, 10).toISOString().split('T')[0],
          AST: null,
          AFI: null,
          PWORK_DAY: 180,
          AWORK_DAY: 0,
          PPER: 0,
          APER: 0,
          PMDAY: 0,
          REMARK_601: '準備開工',
          YPPER: 0,
          DAY_DATE: new Date().toISOString().split('T')[0]
        }
      ];
    }

    onMounted(() => {
      // 延遲初始化，確保 DOM 已完全渲染
      setTimeout(() => {
        fetchProgress();
        // 設置輪詢間隔
        intervalId = setInterval(fetchProgress, 30000);
        
        // 設置 Socket.IO
        socket = io('http://localhost:5000');
        socket.on('connect', () => {
          console.log('已連線到 Socket.IO 伺服器');
        });
        socket.on('update', (data) => {
          socketMessage.value = data.message;
          fetchProgress();
        });
        
        // 添加窗口大小變化監聽器
        window.addEventListener('resize', () => {
          // 簡化 resize 處理邏輯
          setTimeout(() => {
            updateProjectCharts();
          }, 200);
        });
      }, 500);
    })

    onBeforeUnmount(() => {
      if (intervalId) clearInterval(intervalId);
      if (socket) socket.disconnect();
      charts.forEach(chart => {
        if (chart) chart.destroy();
      });
    })

    return {
      progressData,
      socketMessage,
      projectCharts,
      formatDate,
      getStatusText,
      getStatusClass,
      averageProgress,
      aheadProjects,
      behindProjects
    }
  }
}
</script>

<style scoped>
.progress-dashboard {
  background-color: #ffffff;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  padding: 20px;
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  overflow: hidden;
}

.dashboard-title {
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
  font-size: 1.5rem;
}

/* 進度概況卡片樣式 */
.progress-summary {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 15px;
}

.summary-card {
  flex: 1;
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 15px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.summary-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.card-title {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 8px;
}

.card-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
}

/* 專案圖表容器 */
.projects-charts-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
  overflow-y: auto;
  padding-right: 5px;
  flex-grow: 1;
}

.project-chart-card {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.project-chart-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.project-chart-title {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 1rem;
  color: #333;
}

.project-chart-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 0.85rem;
}

.project-id {
  color: #666;
}

.project-status {
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 0.8rem;
}

.project-chart-container {
  height: 180px;
  margin-bottom: 10px;
  position: relative;
}

.project-chart-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  font-size: 0.8rem;
}

/* 添加媒體查詢，確保在不同屏幕尺寸下的響應式布局 */
@media (min-width: 1400px) {
  .projects-charts-container {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  }
}

@media (max-width: 1200px) {
  .projects-charts-container {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
}

@media (max-width: 768px) {
  .projects-charts-container {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  }
  
  .project-chart-container {
    height: 160px;
  }
  
  .project-chart-details {
    font-size: 0.75rem;
  }
}

.detail-item {
  display: flex;
  justify-content: space-between;
}

.detail-label {
  color: #666;
}

.detail-value {
  font-weight: 500;
  color: #333;
}

.status-ahead {
  background-color: rgba(76, 175, 80, 0.2);
  color: #2e7d32;
}

.status-behind {
  background-color: rgba(244, 67, 54, 0.2);
  color: #c62828;
}

.status-completed {
  background-color: rgba(33, 150, 243, 0.2);
  color: #1565c0;
}

.status-ontrack {
  background-color: rgba(255, 193, 7, 0.2);
  color: #f57f17;
}

.realtime-message {
  margin-top: 15px;
  padding: 10px;
  background-color: #e8f5e9;
  border-radius: 8px;
  color: #2e7d32;
  display: flex;
  align-items: center;
  animation: fadeIn 0.5s ease;
}

.message-icon {
  margin-right: 8px;
  font-size: 1.2rem;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>