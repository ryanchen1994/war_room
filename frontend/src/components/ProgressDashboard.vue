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
        <div class="card-title">準時率</div>
        <div class="card-value">{{ onTimeRate }}%</div>
      </div>
      <div class="summary-card">
        <div class="card-title">超前數</div>
        <div class="card-value">{{ aheadProjects }}</div>
      </div>
      <div class="summary-card">
        <div class="card-title">落後數</div>
        <div class="card-value">{{ behindProjects }}</div>
      </div>
    </div>
    
    <!-- 進度誤差説明 -->
    <div class="progress-note">
      <span class="note-icon">ℹ️</span>
      <span class="note-text">預期與實際進度誤差<0.01%，視為符合進度</span>
    </div>
    
    <!-- 專案圖表區域 - 每個專案一個圖表 -->
    <div class="projects-charts-container">
      <div v-for="(project, index) in progressData" :key="project.PROJM_NO" class="project-chart-card">
        <div class="project-header">
          <h3 class="project-chart-title">{{ project.PROJM_NAME || '未命名專案' }}</h3>
          <span class="project-update-date">{{ formatDate(project.DAY_DATE) }}</span>
        </div>
        <div class="project-chart-info">
          <span class="project-id">專案編號: {{ project.PROJM_NO }}</span>
          <span :class="getStatusClass(project)" class="project-status">
            {{ getStatusText(project) }}
            <span v-if="Math.abs(project.APER - project.PPER) >= 0.01" class="progress-diff">
              {{ project.APER > project.PPER ? '+' : '' }}{{ (project.APER - project.PPER).toFixed(1) }}%
            </span>
          </span>
        </div>
        <div class="project-chart-container">
          <canvas :ref="el => { if (el) projectCharts[index] = el }"></canvas>
        </div>
        <div class="project-chart-details">
          <div class="detail-item">
            <span class="detail-label">預計天數:</span>
            <span class="detail-value">{{ project.PWORK_DAY || 0 }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">實際天數:</span>
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
          <!-- 移除了日期項目 -->
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
import { API_BASE_URL, SOCKET_URL, SOCKET_OPTIONS, fetchWithRetry } from '@/config/api.config'

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

    // 計算專案準時率 (符合進度或超前的專案比例)
    const onTimeRate = computed(() => {
      if (progressData.value.length === 0) return 0;
      
      const onTimeProjects = progressData.value.filter(project => {
        // 如果專案未開始，不計入準時率
        if (!project.PPER || !project.APER) return false;
        
        // 計算進度差異的絕對值
        const progressDiff = Math.abs((project.APER || 0) - (project.PPER || 0));
        
        // 符合進度或超前的專案
        return progressDiff < 0.01 || project.APER >= project.PPER;
      });
      
      return Math.round((onTimeProjects.length / progressData.value.length) * 100);
    });

    // 計算超前專案數量
    const aheadProjects = computed(() => {
      return progressData.value.filter(project => 
        (project.APER || 0) > (project.PPER || 0) && Math.abs((project.APER || 0) - (project.PPER || 0)) >= 0.01
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
        //console.error('日期格式化錯誤:', e);
        return '日期錯誤';
      }
    }

    // 獲取專案狀態文字
    const getStatusText = (project) => {
      if (!project.PPER || !project.APER) return '未開始';
      
      // 計算進度差異的絕對值
      const progressDiff = Math.abs((project.APER || 0) - (project.PPER || 0));
      

      
      if (project.BUILD_REM202 && project.BUILD_REM202.includes('超前')) {
        return '超前';
      } else if (project.BUILD_REM202 && project.BUILD_REM202.includes('落後')) {
        // 如果差異小於 0.01%，視為符合進度
        if (progressDiff < 0.01) {
          return '符合進度';
        } else {
          return '落後';
        }
      } else if (project.APER >= 90) {
        return '已完成';
      } else if (project.APER > project.PPER) {
        return '超前';
      } else {
        if (progressDiff < 0.01) {
          return '符合進度';
        } else {
          return '落後';
        }
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
            labels: ['實際進度', '預計差異', '剩餘'],
            datasets: [
              {
                data: [
                  project.APER || 0, 
                  // 如果實際進度超前，使用正值表示超前差異；如果落後，使用正值表示落後差異
                  (project.APER > project.PPER) ? (project.APER - project.PPER) : (project.PPER > project.APER) ? (project.PPER - project.APER) : 0, 
                  // 剩餘進度始終是 100 減去實際進度
                  100 - Math.max(project.APER || 0, project.PPER || 0)
                ],
                backgroundColor: [
                  'rgba(33, 150, 243, 0.5)', // 藍色 - 實際進度
                  // 根據是否超前選擇顏色：超前為綠色，落後為紅色
                  (project.APER > project.PPER) ? 'rgba(76, 175, 80, 0.3)' : 'rgba(244, 67, 54, 0.3)', 
                  'rgba(220, 220, 220, 0.3)'
                ],
                borderColor: [
                  'rgba(33, 150, 243, 0.8)', // 藍色 - 實際進度
                  // 根據是否超前選擇邊框顏色：超前為綠色，落後為紅色
                  (project.APER > project.PPER) ? 'rgba(76, 175, 80, 0.8)' : 'rgba(244, 67, 54, 0.8)', 
                  'rgba(220, 220, 220, 0.5)'
                ],
                borderWidth: 1,
                borderDash: [
                  [0, 0], 
                  [5, 5], // 為差異部分添加虛線效果
                  [0, 0]
                ]
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
                  padding: 5,
                  font: {
                    size: 10
                  }
                },
                display: false
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    const label = context.label || '';
                    const value = parseFloat(context.raw).toFixed(1);
                    
                    if (label === '實際進度') {
                      return `實際進度: ${value}%`;
                    } else if (label === '預計差異') {
                      return `預計差異: ${value}%`;
                    } else {
                      return `剩餘: ${value}%`;
                    }
                  },
                  afterLabel: function(context) {
                    if (context.label === '實際進度') {
                      return `總預計進度: ${parseFloat(project.PPER || 0).toFixed(1)}%`;
                    }
                    return null;
                  }
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
          }, {
            id: 'dashedBorder',
            beforeDraw(chart) {
              const { ctx } = chart;
              const meta = chart.getDatasetMeta(0);
              const project = progressData.value[index];
              
              // 只處理差異部分（索引1）
              if (meta.data[1]) {
                const arc = meta.data[1];
                
                // 保存原始繪圖設置
                ctx.save();
                
                // 清除原始繪製的部分
                ctx.globalCompositeOperation = 'destination-out';
                arc.draw(ctx);
                ctx.globalCompositeOperation = 'source-over';
                
                // 設置虛線樣式
                ctx.setLineDash([3, 3]);
                ctx.lineWidth = 1.5;
                
                // 根據是否超前選擇顏色
                if (project.APER > project.PPER) {
                  ctx.strokeStyle = 'rgba(76, 175, 80, 0.8)'; // 綠色虛線 - 超前
                  ctx.fillStyle = 'rgba(76, 175, 80, 0.2)'; // 綠色填充 - 超前
                } else {
                  ctx.strokeStyle = 'rgba(244, 67, 54, 0.8)'; // 紅色虛線 - 落後
                  ctx.fillStyle = 'rgba(244, 67, 54, 0.2)'; // 紅色填充 - 落後
                }
                
                // 繪製虛線邊框和填充
                ctx.beginPath();
                arc.draw(ctx);
                ctx.stroke();
                ctx.fill();
                
                // 恢復原始設置
                ctx.restore();
              }
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
          bg: 'rgba(33, 150, 243, 0.5)', // 藍色
          border: 'rgba(33, 150, 243, 1)'
        };
      } else if (status === '落後') {
        return {
          bg: 'rgba(244, 67, 54, 0.5)', // 紅色
          border: 'rgba(244, 67, 54, 1)'
        };
      } else if (status === '已完成') {
        return {
          bg: 'rgba(76, 175, 80, 0.5)', // 綠色
          border: 'rgba(76, 175, 80, 1)'
        };
      } else {
        return {
          bg: 'rgba(255, 205, 86, 0.5)', // 黃色
          border: 'rgba(255, 205, 86, 1)'
        };
      }
    };


    const fetchProgress = async () => {
      try {
        // 設定 API 請求的身分驗證資訊
        const authConfig = {
          auth: {
            username: 'admin', // 使用配置的用户名
            password: 'thm' // 使用配置的密碼
          },
          headers: {
            'Content-Type': 'application/json'
          }
        };

        // 使用 axios 直接請求，以便傳遞身分驗證資訊
        const response = await axios.get(`${API_BASE_URL}/api/remar`, authConfig);
        
        // 檢查回應格式
        let dataArray = [];
        if (response && response.data) {
          if (Array.isArray(response.data)) {
            dataArray = response.data;
          } else if (Array.isArray(response.data.data)) {
            dataArray = response.data.data;
          } else if (typeof response.data === 'object' && !Array.isArray(response.data)) {
            // 如果是單一物件，轉換成陣列
            dataArray = [response.data];
          }
        }

        if (dataArray.length > 0) {
          progressData.value = dataArray.map(project => {
            // 確保數值型別正確
            return {
              ...project,
              PWORK_DAY: parseInt(project.PWORK_DAY) || 0,
              AWORK_DAY: parseInt(project.AWORK_DAY) || 0,
              PPER: parseFloat(parseFloat(project.PPER || 0).toFixed(3)) || 0,
              APER: parseFloat(parseFloat(project.APER || 0).toFixed(3)) || 0,
              PMDAY: parseInt(project.PMDAY) || 0,
              YPPER: parseFloat(parseFloat(project.YPPER || 0).toFixed(3)) || 0
            };
          });

          // 延遲更新圖表，確保 DOM 已更新
          setTimeout(() => {
            updateProjectCharts();
          }, 100);
        } else {
          console.warn('API 未返回有效數據，使用模擬數據');
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
      setTimeout(() => {
        fetchProgress();
        intervalId = setInterval(fetchProgress, 30000);
        
        window.addEventListener('resize', () => {
          setTimeout(() => {
            updateProjectCharts();
          }, 200);
        });
      }, 500);
    });

    onBeforeUnmount(() => {
      if (intervalId) clearInterval(intervalId);
      // if (socket) socket.disconnect();  // 移除這行
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
      onTimeRate,
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
  overflow: hidden; /* 改回 hidden，讓內部元素可以使用捲動軸 */
}

/* 進度概況卡片樣式 */
.progress-summary {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px; /* 減少底部間距 */
  gap: 15px;
  flex-shrink: 0; /* 防止摘要卡片被壓縮 */
}

/* 進度誤差説明樣式 */
.progress-note {
  display: flex;
  align-items: center;
  font-size: 0.8rem;
  color: #666;
  margin-bottom: 10px;
  padding: 4px 8px;
  background-color: #f5f5f5;
  border-radius: 4px;
  flex-shrink: 0;
}

.note-icon {
  margin-right: 6px;
  font-size: 0.9rem;
}

.note-text {
  font-style: italic;
}

/* 專案圖表容器 */
.projects-charts-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 15px;
  overflow-y: auto; /* 添加垂直捲動軸 */
  padding-right: 5px; /* 為捲動軸預留空間 */
  flex-grow: 1;
  max-height: calc(100% - 150px); /* 調整最大高度，為新增的説明文字留出空間 */
}

.project-chart-card {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  height: auto;
}

.project-chart-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5px;
  font-size: 0.75rem;
}

/* 修改日期項目樣式，確保在同一行 */
.detail-item {
  display: flex;
  justify-content: space-between;
  white-space: nowrap; /* 防止換行 */
  overflow: hidden; /* 隱藏溢出內容 */
}

.detail-label {
  color: #666;
  flex-shrink: 0; /* 防止標籤被壓縮 */
  margin-right: 5px; /* 與值之間的間距 */
}

.detail-value {
  font-weight: 500;
  color: #333;
  text-overflow: ellipsis; /* 文字溢出時顯示省略號 */
  overflow: hidden; /* 隱藏溢出內容 */
}

/* 特別處理日期項目 */
.detail-item.date-item {
  grid-column: span 2; /* 日期項目橫跨兩列 */
}
/* 自定義捲動軸樣式 */
.projects-charts-container::-webkit-scrollbar {
  width: 6px;
}

.projects-charts-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.projects-charts-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.projects-charts-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.realtime-message {
  margin-top: 10px;
  padding: 8px 10px;
  background-color: #e8f5e9;
  border-radius: 8px;
  color: #2e7d32;
  display: flex;
  align-items: center;
  animation: fadeIn 0.5s ease;
  flex-shrink: 0; /* 防止消息被壓縮 */
}
.dashboard-title {
  margin-top: 0;
  margin-bottom: 15px; /* 減少底部間距 */
  color: #333;
  font-size: 1.5rem;
}

/* 進度概況卡片樣式 */
.progress-summary {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px; /* 減少底部間距 */
  gap: 12px;
}

.summary-card {
  flex: 1;
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 1px;
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
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); /* 減小最小寬度 */
  gap: 12px; /* 減少間距 */
  margin-bottom: 15px; /* 減少底部間距 */
  padding-right: 0; /* 移除右側內邊距 */
  flex-grow: 1;
}

.project-chart-card {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 10px; /* 減少內邊距 */
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
  margin-bottom: 4px; /* 減少底部間距 */
  font-size: 1rem; /* 減小字體大小 */
  color: #333;
}

.project-chart-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px; /* 減少底部間距 */
  font-size: 0.8rem; /* 減小字體大小 */
}

.project-chart-container {
  height: 140px; /* 減小圖表高度 */
  margin-bottom: 8px; /* 減少底部間距 */
  position: relative;
}

.project-chart-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3px; /* 減少間距 */
  font-size: 0.75rem; /* 減小字體大小 */
}

/* 添加媒體查詢，確保在不同屏幕尺寸下的響應式佈局 */
@media (min-width: 1400px) {
  .projects-charts-container {
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  }
}

@media (max-width: 1200px) {
  .projects-charts-container {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  }
  
  .project-chart-container {
    height: 140px;
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

/* 專案狀態樣式 */
.project-status {
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 4px;
}
.progress-diff {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 1px 4px;
  border-radius: 8px;
  background-color: rgba(255, 255, 255, 0.5);
}
.status-ahead .progress-diff {
  color: #1b5e20;
}
.status-behind .progress-diff {
  color: #b71c1c;
}
.status-ontrack .progress-diff {
  color: #e65100;
}
.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.project-chart-title {
  margin: 0;
  font-size: 1rem;
  color: #333;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.project-update-date {
  font-size: 0.7rem;
  color: #888;
  margin-left: 8px;
  white-space: nowrap;
}
/* 移除舊的日期項目樣式 */
.detail-item.date-item {
  grid-column: span 2;
  white-space: nowrap;
  overflow: hidden;
  padding: 2px 0;
  font-size: 0.7rem;
}
.detail-item.date-item .detail-value {
  text-overflow: ellipsis;
  overflow: hidden;
}
.detail-label {
  color: #666;
  flex-shrink: 0; /* 防止標籤被壓縮 */
  margin-right: 5px; /* 與值之間的間距 */
}
.detail-value {
  font-weight: 500;
  color: #333;
  text-overflow: ellipsis; /* 文字溢出時顯示省略號 */
  overflow: hidden; /* 隱藏溢出內容 */
}
/* 特別處理日期項目 */
.detail-item.date-item {
  grid-column: span 2; /* 日期項目橫跨兩列 */
}
/* 自定義捲動軸樣式 */
.projects-charts-container::-webkit-scrollbar {
  width: 6px;
}
.projects-charts-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}
.projects-charts-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}
.projects-charts-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
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