<template>
  <div class="progress-dashboard">
    <h2 class="dashboard-title">工程進度追蹤</h2>
    
    <!-- 圖表區域 -->
    <div class="chart-container">
      <canvas ref="progressCanvas"></canvas>
    </div>
    
    <!-- 專案列表 -->
    <div class="project-list">
      <div class="project-item" v-for="item in progressData" :key="item.PROJM_NO">
        <!-- 現有內容保持不變 -->
        <div class="project-header">
          <span class="project-id">{{ item.PROJM_NO }}</span>
          <span class="project-name">{{ item.PROJM_SNAME }}</span>
        </div>
        <!-- 其餘內容保持不變 -->
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
import { ref, onMounted, onBeforeUnmount } from 'vue'

export default {
  name: 'ProgressDashboard',
  setup() {
    const progressData = ref([])
    const socketMessage = ref('')
    const progressCanvas = ref(null)
    const chart = ref(null)
    let intervalId = null
    let socket = null

    const formatDate = (dateString) => {
      if (!dateString) return '未設定';
      try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return '日期格式錯誤';
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
      } catch (e) {
        console.error('日期格式化錯誤:', e);
        return '日期錯誤';
      }
    }

    const updateChart = () => {
      try {
        // 檢查 canvas 元素是否存在
        if (!progressCanvas.value) {
          console.warn('Canvas 元素不存在，無法更新圖表');
          return;
        }

        // 確保 canvas 的父元素存在
        if (!progressCanvas.value.parentElement) {
          console.warn('Canvas 父元素不存在，無法更新圖表');
          return;
        }

        // 設置 Canvas 尺寸
        const parentWidth = progressCanvas.value.parentElement.clientWidth;
        const parentHeight = progressCanvas.value.parentElement.clientHeight || 350;
        
        progressCanvas.value.style.width = '100%';
        progressCanvas.value.style.height = '100%';
        progressCanvas.value.width = parentWidth;
        progressCanvas.value.height = parentHeight;

        if (!chart.value) {
          const ctx = progressCanvas.value.getContext('2d');
          if (!ctx) {
            console.error('無法獲取 Canvas 上下文');
            return;
          }

          chart.value = new Chart(ctx, {
            type: 'bar',
            data: {
              labels: progressData.value.map(item => item.PROJM_SNAME),
              datasets: [
                {
                  label: '預定工作天',
                  data: progressData.value.map(item => item.WORK_DAY),
                  backgroundColor: 'rgba(54, 162, 235, 0.7)',
                  borderColor: 'rgba(54, 162, 235, 1)',
                  borderWidth: 1
                },
                {
                  label: '實際工作天',
                  data: progressData.value.map(item => item.ACTUAL_WORK_DAY || 0),
                  backgroundColor: 'rgba(75, 192, 192, 0.7)',
                  borderColor: 'rgba(75, 192, 192, 1)',
                  borderWidth: 1
                }
              ]
            },
            options: {
              indexAxis: 'y',
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                title: {
                  display: true,
                  text: '專案工作天數對比',
                  font: {
                    size: 16,
                    weight: 'bold'
                  }
                },
                legend: {
                  position: 'bottom'
                },
                tooltip: {
                  callbacks: {
                    label: function(context) {
                      return context.dataset.label + ': ' + context.raw + ' 天';
                    }
                  }
                }
              },
              scales: {
                x: {
                  beginAtZero: true,
                  title: {
                    display: true,
                    text: '工作天數'
                  }
                },
                y: {
                  title: {
                    display: true,
                    text: '專案名稱'
                  }
                }
              }
            }
          });
          console.log('圖表創建成功');
        } else {
          // 更新圖表數據
          chart.value.data.labels = progressData.value.map(item => item.PROJM_SNAME);
          chart.value.data.datasets[0].data = progressData.value.map(item => item.WORK_DAY);
          chart.value.data.datasets[1].data = progressData.value.map(item => item.ACTUAL_WORK_DAY || 0);
          chart.value.update('none'); // 使用 'none' 模式更新，減少動畫
          console.log('圖表更新成功');
        }
      } catch (error) {
        console.error('圖表處理過程中發生錯誤:', error);
        // 如果出錯，嘗試重新創建圖表
        if (chart.value) {
          try {
            chart.value.destroy();
          } catch (e) {
            // 忽略銷毀時的錯誤
          }
          chart.value = null;
        }
      }
    }

    const fetchProgress = async () => {
      try {
        console.log('開始獲取進度數據...');
        const response = await axios.get('http://localhost:5000/api/progress');
        
        if (Array.isArray(response.data)) {
          progressData.value = response.data.map(project => {
            // 確保日期格式正確
            if (project.PST && typeof project.PST === 'string') {
              project.PST = project.PST.replace(/T.*$/, '');
            }
            if (project.PFI && typeof project.PFI === 'string') {
              project.PFI = project.PFI.replace(/T.*$/, '');
            }
            
            // 確保數值型別正確
            project.WORK_DAY = parseInt(project.WORK_DAY) || 0;
            project.ACTUAL_WORK_DAY = parseInt(project.ACTUAL_WORK_DAY) || 0;
            
            return project;
          });
          
          // 直接更新圖表，不使用 nextTick
          updateChart();
        } else {
          console.error('API 返回的數據不是數組格式:', response.data);
          // 使用模擬數據
          progressData.value = generateMockData();
          updateChart();
        }
      } catch (error) {
        console.error('獲取進度數據失敗:', error);
        // 使用模擬數據
        progressData.value = generateMockData();
        updateChart();
      }
    }

    // 生成模擬數據函數
    const generateMockData = () => {
      const today = new Date();
      return [
        {
          PROJM_NO: 'P2023001',
          PROJM_SNAME: '台北商辦大樓',
          PST: new Date(today.getFullYear(), today.getMonth() - 2, 15).toISOString().split('T')[0],
          PFI: new Date(today.getFullYear(), today.getMonth() + 4, 20).toISOString().split('T')[0],
          WORK_DAY: 180,
          ACTUAL_WORK_DAY: 60
        },
        // 其他模擬數據...
      ];
    }

    const calculateProgress = (project) => {
      if (!project.ACTUAL_WORK_DAY || !project.WORK_DAY) return 0;
      const progress = Math.min(Math.round((project.ACTUAL_WORK_DAY / project.WORK_DAY) * 100), 100);
      return progress;
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
          if (chart.value) {
            try {
              chart.value.resize();
            } catch (e) {
              console.warn('調整圖表大小時出錯');
              // 不要立即重新創建圖表，避免頻繁重建
            }
          }
        });
      }, 500);
    })

    onBeforeUnmount(() => {
      if (intervalId) clearInterval(intervalId)
      if (socket) socket.disconnect()
      if (chart.value) chart.value.destroy()
    })

    return {
      progressData,
      socketMessage,
      progressCanvas,
      formatDate,
      calculateProgress
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

.chart-container {
  position: relative;
  width: 100%;
  height: 350px;
  min-height: 250px;
  margin: 0 0 20px 0;
  padding: 0;
  overflow: hidden;
  background-color: #f9f9f9;
  border-radius: 8px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  box-sizing: border-box;
}

canvas {
  max-width: 100%;
  max-height: 100%;
}

.project-list {
  margin-top: 20px;
  flex-grow: 1;
  overflow-y: auto; /* 允許項目列表捲動 */
  border-radius: 8px;
  background-color: #f9f9f9;
}

/* 其他樣式保持不變 */
</style>