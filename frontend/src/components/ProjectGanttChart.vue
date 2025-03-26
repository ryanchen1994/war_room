<template>
  <div class="gantt-chart-view">
    <h2 class="dashboard-title">工程進度甘特圖</h2>
    
    <div class="chart-controls">
      <div class="filter-group">
        <label for="project-filter">專案狀態:</label>
        <select id="project-filter" v-model="selectedFilter" @change="filterProjects">
          <option value="all">全部專案</option>
          <option value="inProgress">進行中</option>
          <option value="completed">已完成</option>
          <option value="planned">規劃中</option>
        </select>
      </div>
    </div>
    
    <div class="chart-container">
      <canvas ref="ganttCanvas"></canvas>
    </div>
    
    <div class="project-timeline" v-if="projects.length > 0">
      <div class="timeline-header">
        <div class="timeline-project">專案名稱</div>
        <div class="timeline-dates">
          <div class="timeline-start">開始日期</div>
          <div class="timeline-end">預計完成</div>
          <div class="timeline-progress">進度</div>
        </div>
      </div>
      
      <div class="timeline-item" v-for="project in projects" :key="project.PROJM_NO">
        <div class="timeline-project">{{ project.PROJM_SNAME }}</div>
        <div class="timeline-dates">
          <div class="timeline-start">{{ formatDate(project.PST) }}</div>
          <div class="timeline-end">{{ formatDate(project.PFI) }}</div>
          <div class="timeline-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{width: calculateProgress(project) + '%'}"></div>
            </div>
            <span class="progress-text">{{ calculateProgress(project) }}%</span>
          </div>
        </div>
      </div>
    </div>
    
    <p v-else class="no-data">暫無專案資料</p>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, nextTick, computed, watch } from 'vue'
import { Chart } from 'chart.js/auto'
import axios from 'axios'

export default {
  name: 'ProjectGanttChart',
  setup() {
    const ganttCanvas = ref(null)
    const chart = ref(null)
    const resizeObserver = ref(null)
    const chartInitialized = ref(false)
    const allProjects = ref([])
    const selectedFilter = ref('all')
    
    // 根據篩選條件過濾專案
    const projects = computed(() => {
      if (selectedFilter.value === 'all') {
        return allProjects.value
      } else if (selectedFilter.value === 'inProgress') {
        return allProjects.value.filter(p => calculateProgress(p) > 0 && calculateProgress(p) < 100)
      } else if (selectedFilter.value === 'completed') {
        return allProjects.value.filter(p => calculateProgress(p) >= 100)
      } else if (selectedFilter.value === 'planned') {
        return allProjects.value.filter(p => calculateProgress(p) === 0)
      }
      return allProjects.value
    })
    
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
    
    // 從API獲取專案進度數據
    const fetchProjects = async () => {
      try {
        console.log('開始獲取專案進度數據...');
        const response = await axios.get('http://localhost:5000/api/progress');
        console.log('獲取到的數據:', response.data);
        
        if (Array.isArray(response.data) && response.data.length > 0) {
          allProjects.value = response.data.map(project => {
            // 確保日期格式正確
            if (project.PST && typeof project.PST === 'string') {
              // 處理 "20250725" 格式的日期
              if (project.PST.length === 8 && !project.PST.includes('-')) {
                const year = project.PST.substring(0, 4);
                const month = project.PST.substring(4, 6);
                const day = project.PST.substring(6, 8);
                project.PST = `${year}-${month}-${day}`;
              } else {
                project.PST = project.PST.replace(/T.*$/, '');
              }
            }
            
            if (project.PFI && typeof project.PFI === 'string') {
              // 處理 "20250725" 格式的日期
              if (project.PFI.length === 8 && !project.PFI.includes('-')) {
                const year = project.PFI.substring(0, 4);
                const month = project.PFI.substring(4, 6);
                const day = project.PFI.substring(6, 8);
                project.PFI = `${year}-${month}-${day}`;
              } else {
                project.PFI = project.PFI.replace(/T.*$/, '');
              }
            }
            
            // 確保數值型別正確
            project.WORK_DAY = parseInt(project.WORK_DAY) || 0;
            project.ACTUAL_WORK_DAY = parseInt(project.ACTUAL_WORK_DAY) || 0;
            
            return project;
          });
        } else {
          console.error('API 返回的數據不是有效數組:', response.data);
          // 使用模擬數據
          allProjects.value = generateMockData();
        }
        
        nextTick(() => {
          setTimeout(() => {
            createGanttChart();
          }, 300);
        });
      } catch (error) {
        console.error('獲取專案進度資料失敗:', error);
        // 使用模擬數據
        allProjects.value = generateMockData();
        nextTick(() => {
          setTimeout(() => {
            createGanttChart();
          }, 300);
        });
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
          ACTUAL_WORK_DAY: 60,
          STATUS: 'active'
        },
        // 其他模擬數據...
      ];
    }
    
    const calculateProgress = (project) => {
      if (!project.ACTUAL_WORK_DAY || !project.WORK_DAY) return 0
      const progress = Math.min(Math.round((project.ACTUAL_WORK_DAY / project.WORK_DAY) * 100), 100)
      return progress
    }
    
    const filterProjects = () => {
      // 重新渲染圖表
      createGanttChart()
    }
    
    // 創建甘特圖
    const createGanttChart = () => {
      if (!ganttCanvas.value) return
      
      if (chart.value) {
        chart.value.destroy()
        chart.value = null
      }
      
      nextTick(() => {
        const ctx = ganttCanvas.value.getContext('2d')
        
        if (!ctx) {
          console.error('無法獲取 canvas 上下文')
          return
        }
        
        // 準備甘特圖數據
        const today = new Date()
        const labels = projects.value.map(p => p.PROJM_SNAME)
        const startDates = projects.value.map(p => new Date(p.PST || today))
        const endDates = projects.value.map(p => new Date(p.PFI || today))
        
        // 計算每個專案的時間長度（以天為單位）
        const durations = projects.value.map((p, i) => {
          const start = startDates[i]
          const end = endDates[i]
          return Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)))
        })
        
        // 計算已完成的時間長度
        const completedDurations = projects.value.map((p, i) => {
          return Math.ceil(durations[i] * (calculateProgress(p) / 100))
        })
        
        // 創建圖表
        chart.value = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [
              {
                label: '已完成',
                data: completedDurations,
                backgroundColor: 'rgba(46, 204, 113, 0.7)',
                borderColor: 'rgba(46, 204, 113, 1)',
                borderWidth: 1,
                borderRadius: 4,
                barPercentage: 0.8
              },
              {
                label: '剩餘',
                data: durations.map((d, i) => d - completedDurations[i]),
                backgroundColor: 'rgba(189, 195, 199, 0.7)',
                borderColor: 'rgba(189, 195, 199, 1)',
                borderWidth: 1,
                borderRadius: {
                  topLeft: 0,
                  topRight: 4,
                  bottomRight: 4,
                  bottomLeft: 0
                },
                barPercentage: 0.8
              }
            ]
          },
          options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            animation: {
              duration: 1000,
              easing: 'easeOutQuad'
            },
            plugins: {
              title: {
                display: true,
                text: '專案進度甘特圖',
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
                    const projectIndex = context.dataIndex
                    const project = projects.value[projectIndex]
                    
                    if (context.datasetIndex === 0) {
                      return `已完成: ${calculateProgress(project)}%`
                    } else {
                      return `剩餘: ${100 - calculateProgress(project)}%`
                    }
                  },
                  footer: function(tooltipItems) {
                    const projectIndex = tooltipItems[0].dataIndex
                    const project = projects.value[projectIndex]
                    return [
                      `開始日期: ${formatDate(project.PST)}`,
                      `預計完成: ${formatDate(project.PFI)}`,
                      `工作天數: ${project.WORK_DAY} 天`
                    ]
                  }
                }
              }
            },
            scales: {
              x: {
                stacked: true,
                title: {
                  display: true,
                  text: '工作天數'
                }
              },
              y: {
                stacked: true,
                title: {
                  display: true,
                  text: '專案名稱'
                }
              }
            }
          }
        })
        
        chartInitialized.value = true
      })
    }
    
    // 處理視窗大小變化
    const handleResize = () => {
      if (!chartInitialized.value) return
      
      setTimeout(() => {
        createGanttChart()
      }, 200)
    }
    
    onMounted(() => {
      nextTick(() => {
        fetchProjects()
        
        if (window.ResizeObserver) {
          resizeObserver.value = new ResizeObserver(() => {
            if (chartInitialized.value) {
              handleResize()
            }
          })
          
          if (ganttCanvas.value && ganttCanvas.value.parentElement) {
            resizeObserver.value.observe(ganttCanvas.value.parentElement)
          }
        }
        
        window.addEventListener('resize', handleResize)
      })
    })
    
    // 監聽篩選條件變化
    watch(selectedFilter, () => {
      filterProjects()
    })
    
    onBeforeUnmount(() => {
      if (chart.value) {
        chart.value.destroy()
        chart.value = null
      }
      
      if (resizeObserver.value) {
        resizeObserver.value.disconnect()
      }
      
      window.removeEventListener('resize', handleResize)
    })
    
    return {
      ganttCanvas,
      projects,
      selectedFilter,
      formatDate,
      calculateProgress,
      filterProjects
    }
  }
}
</script>

<style scoped>
.gantt-chart-view {
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
  color: #2c3e50;
  font-size: 1.5rem;
  margin-bottom: 20px;
  text-align: left;
  border-bottom: 2px solid #f0f0f0;
  padding-bottom: 10px;
  flex-shrink: 0;
}

.chart-container {
  position: relative;
  width: 100%;
  flex-grow: 1;
  min-height: 250px;
  background-color: #f9f9f9;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
  box-sizing: border-box;
}

canvas {
  max-width: 100%;
  max-height: 100%;
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

.chart-controls {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 15px;
  flex-shrink: 0;
}

.filter-group {
  display: flex;
  align-items: center;
}

.filter-group label {
  margin-right: 8px;
  font-size: 0.9rem;
  color: #7f8c8d;
}

.filter-group select {
  padding: 6px 10px;
  border-radius: 4px;
  border: 1px solid #ddd;
  background-color: #f8f9fa;
  font-size: 0.9rem;
}

.chart-container {
  position: relative;
  width: 100%;
  height: 350px;
  min-height: 250px;
  margin-bottom: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}

.project-timeline {
  flex-grow: 1;
  overflow-y: auto;
  border-top: 1px solid #eaeaea;
  margin-top: 10px;
}

.timeline-header {
  display: flex;
  padding: 10px 15px;
  background-color: #f8f9fa;
  font-weight: bold;
  border-bottom: 1px solid #eaeaea;
  position: sticky;
  top: 0;
  z-index: 1;
}

.timeline-item {
  display: flex;
  padding: 12px 15px;
  border-bottom: 1px solid #eaeaea;
  transition: background-color 0.2s;
}

.timeline-item:hover {
  background-color: #f5f7fa;
}

.timeline-project {
  flex: 2;
  font-weight: 500;
}

.timeline-dates {
  flex: 3;
  display: flex;
}

.timeline-start, .timeline-end {
  flex: 1;
  color: #7f8c8d;
}

.timeline-progress {
  flex: 1;
  display: flex;
  align-items: center;
}

.progress-bar {
  flex-grow: 1;
  height: 8px;
  background-color: #ecf0f1;
  border-radius: 4px;
  overflow: hidden;
  margin-right: 10px;
}

.progress-fill {
  height: 100%;
  background-color: #2ecc71;
  border-radius: 4px;
}

.progress-text {
  min-width: 40px;
  text-align: right;
  font-size: 0.9rem;
  font-weight: 500;
}

.no-data {
  text-align: center;
  color: #7f8c8d;
  margin-top: 30px;
  font-size: 1.1rem;
}

/* 捲動條樣式 */
.project-timeline::-webkit-scrollbar {
  width: 8px;
}

.project-timeline::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.project-timeline::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.project-timeline::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>