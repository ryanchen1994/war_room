<template>
  <div class="weekly-report-view">
    <h2 class="dashboard-title">工程週報</h2>
    
    <div class="report-controls">
      <div class="filter-group">
        <label for="report-filter">報表類型:</label>
        <select id="report-filter" v-model="selectedReportType">
          <option value="gantt">甘特圖</option>
          <option value="progress">進度表</option>
          <option value="horizontal">水平進度</option>
          <option value="operation">作業進度</option>
        </select>
      </div>
      <div class="filter-group">
        <label for="project-filter">專案:</label>
        <select id="project-filter" v-model="selectedProject">
          <option v-for="project in projects" :key="project.id" :value="project.id">
            {{ project.name }}
          </option>
        </select>
      </div>
    </div>
    
    <!-- 甘特圖報表 -->
    <div v-if="selectedReportType === 'gantt'" class="report-container">
      <div class="chart-container">
        <canvas ref="ganttCanvas"></canvas>
      </div>
      <div class="report-details">
        <h3>專案進度摘要</h3>
        <div class="progress-summary">
          <div class="summary-item">
            <div class="summary-label">總進度</div>
            <div class="summary-value">{{ getCurrentProject()?.progress || 0 }}%</div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{width: (getCurrentProject()?.progress || 0) + '%'}"></div>
            </div>
          </div>
          <div class="summary-item">
            <div class="summary-label">預計完成日</div>
            <div class="summary-value">{{ formatDate(getCurrentProject()?.endDate || '') }}</div>
          </div>
          <div class="summary-item">
            <div class="summary-label">實際工作天數</div>
            <div class="summary-value">{{ getCurrentProject()?.actualDays || 0 }} / {{ getCurrentProject()?.totalDays || 0 }} 天</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 進度表報表 -->
    <div v-if="selectedReportType === 'progress'" class="report-container">
      <div class="table-container">
        <table class="progress-table">
          <thead>
            <tr>
              <th>工項</th>
              <th>計畫起始</th>
              <th>計畫完成</th>
              <th>實際起始</th>
              <th>實際完成</th>
              <th>進度</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in getCurrentProject().workItems" :key="index">
              <td>{{ item.name }}</td>
              <td>{{ formatDate(item.plannedStart) }}</td>
              <td>{{ formatDate(item.plannedEnd) }}</td>
              <td>{{ formatDate(item.actualStart) }}</td>
              <td>{{ formatDate(item.actualEnd) || '進行中' }}</td>
              <td>
                <div class="inline-progress">
                  <div class="inline-progress-bar">
                    <div class="inline-progress-fill" :style="{width: item.progress + '%'}"></div>
                  </div>
                  <span>{{ item.progress }}%</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- 水平進度報表 -->
    <div v-if="selectedReportType === 'horizontal'" class="report-container">
      <div class="chart-container">
        <canvas ref="horizontalCanvas"></canvas>
      </div>
    </div>
    
    <!-- 作業進度報表 -->
    <div v-if="selectedReportType === 'operation'" class="report-container">
      <div class="table-container">
        <table class="operation-table">
          <thead>
            <tr>
              <th>作業項目</th>
              <th>單位</th>
              <th>預計數量</th>
              <th>已完成</th>
              <th>完成率</th>
              <th>備註</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in getCurrentProject().operationItems" :key="index">
              <td>{{ item.name }}</td>
              <td>{{ item.unit }}</td>
              <td>{{ item.plannedQuantity }}</td>
              <td>{{ item.completedQuantity }}</td>
              <td>
                <div class="inline-progress">
                  <div class="inline-progress-bar">
                    <div class="inline-progress-fill" :style="{width: item.completionRate + '%'}"></div>
                  </div>
                  <span>{{ item.completionRate }}%</span>
                </div>
              </td>
              <td>{{ item.notes }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, nextTick, computed, watch } from 'vue'
import { Chart } from 'chart.js/auto'
import axios from 'axios'

export default {
  name: 'WeeklyReport',
  setup() {
    const ganttCanvas = ref(null)
    const horizontalCanvas = ref(null)
    const ganttChart = ref(null)
    const horizontalChart = ref(null)
    const resizeObserver = ref(null)
    const selectedReportType = ref('gantt')
    const selectedProject = ref(null)
    let resizeTimeout = null // 添加這一行
    let chartInitialized = ref(false) // 添加標記，避免重複初始化
    
    // 模擬數據 - 基於圖片中的資料
    const projects = ref([
      {
        id: 'P001',
        name: '台北商辦大樓',
        progress: 65,
        startDate: '20230315',
        endDate: '20240520',
        actualDays: 180,
        totalDays: 280,
        workItems: [
          { 
            name: '基礎工程', 
            plannedStart: '20230315', 
            plannedEnd: '20230615', 
            actualStart: '20230320', 
            actualEnd: '20230620', 
            progress: 100 
          },
          { 
            name: '結構工程', 
            plannedStart: '20230601', 
            plannedEnd: '20231015', 
            actualStart: '20230610', 
            actualEnd: '20231020', 
            progress: 100 
          },
          { 
            name: '機電工程', 
            plannedStart: '20230815', 
            plannedEnd: '20240215', 
            actualStart: '20230825', 
            actualEnd: null, 
            progress: 70 
          },
          { 
            name: '裝修工程', 
            plannedStart: '20231115', 
            plannedEnd: '20240415', 
            actualStart: '20231125', 
            actualEnd: null, 
            progress: 40 
          },
          { 
            name: '驗收', 
            plannedStart: '20240415', 
            plannedEnd: '20240520', 
            actualStart: null, 
            actualEnd: null, 
            progress: 0 
          }
        ],
        operationItems: [
          { name: '鋼筋綁紮', unit: '噸', plannedQuantity: 450, completedQuantity: 450, completionRate: 100, notes: '已完成' },
          { name: '模板組立', unit: '㎡', plannedQuantity: 12000, completedQuantity: 12000, completionRate: 100, notes: '已完成' },
          { name: '混凝土澆置', unit: '㎥', plannedQuantity: 8500, completedQuantity: 8500, completionRate: 100, notes: '已完成' },
          { name: '機電管線', unit: '式', plannedQuantity: 1, completedQuantity: 0.7, completionRate: 70, notes: '進行中' },
          { name: '內部裝修', unit: '㎡', plannedQuantity: 9500, completedQuantity: 3800, completionRate: 40, notes: '進行中' }
        ]
      },
      {
        id: 'P002',
        name: '新竹科技園區',
        progress: 80,
        startDate: '20230110',
        endDate: '20240310',
        actualDays: 220,
        totalDays: 270,
        workItems: [
          { 
            name: '基礎工程', 
            plannedStart: '20230110', 
            plannedEnd: '20230410', 
            actualStart: '20230115', 
            actualEnd: '20230415', 
            progress: 100 
          },
          { 
            name: '結構工程', 
            plannedStart: '20230401', 
            plannedEnd: '20230815', 
            actualStart: '20230405', 
            actualEnd: '20230820', 
            progress: 100 
          },
          { 
            name: '機電工程', 
            plannedStart: '20230715', 
            plannedEnd: '20231215', 
            actualStart: '20230720', 
            actualEnd: '20231220', 
            progress: 100 
          },
          { 
            name: '裝修工程', 
            plannedStart: '20231015', 
            plannedEnd: '20240215', 
            actualStart: '20231020', 
            actualEnd: null, 
            progress: 75 
          },
          { 
            name: '驗收', 
            plannedStart: '20240215', 
            plannedEnd: '20240310', 
            actualStart: null, 
            actualEnd: null, 
            progress: 0 
          }
        ],
        operationItems: [
          { name: '鋼筋綁紮', unit: '噸', plannedQuantity: 380, completedQuantity: 380, completionRate: 100, notes: '已完成' },
          { name: '模板組立', unit: '㎡', plannedQuantity: 10500, completedQuantity: 10500, completionRate: 100, notes: '已完成' },
          { name: '混凝土澆置', unit: '㎥', plannedQuantity: 7200, completedQuantity: 7200, completionRate: 100, notes: '已完成' },
          { name: '機電管線', unit: '式', plannedQuantity: 1, completedQuantity: 1, completionRate: 100, notes: '已完成' },
          { name: '內部裝修', unit: '㎡', plannedQuantity: 8200, completedQuantity: 6150, completionRate: 75, notes: '進行中' }
        ]
      }
    ])
    
    // 初始化選擇第一個專案
    if (projects.value.length > 0) {
      selectedProject.value = projects.value[0].id
    }
    
    // 獲取當前選擇的專案
    const getCurrentProject = () => {
      return projects.value.find(p => p.id === selectedProject.value) || projects.value[0]
    }
    
    // 日期格式化
    const formatDate = (dateString) => {
      if (!dateString) return '未設定'
      try {
        // 處理 "20250725" 格式的日期
        if (typeof dateString === 'string' && dateString.length === 8 && !dateString.includes('-')) {
          const year = dateString.substring(0, 4)
          const month = dateString.substring(4, 6)
          const day = dateString.substring(6, 8)
          return `${year}-${month}-${day}`
        }
        
        // 處理標準日期格式
        const date = new Date(dateString)
        if (isNaN(date.getTime())) return '日期格式錯誤'
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
      } catch (e) {
        console.error('日期格式化錯誤:', e)
        return '日期錯誤'
      }
    }
    
    // 創建甘特圖
    const createGanttChart = () => {
      console.log('開始創建甘特圖...')
      
      if (!ganttCanvas.value) {
        console.error('甘特圖 Canvas 元素不存在')
        return
      }
      
      // 避免重複創建
      if (ganttChart.value) {
        console.log('甘特圖已存在，不重複創建')
        return
      }
      
      // 確保 Canvas 元素已經渲染並且可見
      if (ganttCanvas.value.offsetParent === null) {
        console.warn('甘特圖 Canvas 元素不可見，延遲創建')
        setTimeout(createGanttChart, 500)
        return
      }
      
      try {
        const ctx = ganttCanvas.value.getContext('2d')
        
        if (!ctx) {
          console.error('無法獲取 Canvas 上下文')
          return
        }
        
        console.log('成功獲取 Canvas 上下文')
        
        // 設置 Canvas 尺寸
        if (ganttCanvas.value.parentElement) {
          const parentWidth = ganttCanvas.value.parentElement.clientWidth
          const parentHeight = ganttCanvas.value.parentElement.clientHeight || 350
          
          console.log(`父元素尺寸: ${parentWidth}x${parentHeight}`)
          
          // 使用 style 屬性設置尺寸
          ganttCanvas.value.style.width = '100%'
          ganttCanvas.value.style.height = '100%'
          
          // 設置實際像素尺寸
          ganttCanvas.value.width = parentWidth
          ganttCanvas.value.height = parentHeight
        }
        
        const currentProject = getCurrentProject()
        console.log('當前項目:', currentProject)
        
        if (!currentProject || !currentProject.workItems || currentProject.workItems.length === 0) {
          console.error('當前項目或工作項不存在或為空')
          // 創建一個空的圖表，顯示無數據
          ganttChart.value = new Chart(ctx, {
            type: 'bar',
            data: {
              labels: ['無數據'],
              datasets: [{
                label: '無可用數據',
                data: [0],
                backgroundColor: 'rgba(200, 200, 200, 0.5)'
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                title: {
                  display: true,
                  text: '無可用數據',
                  font: { size: 16 }
                }
              }
            }
          })
          chartInitialized.value = true // 標記圖表已初始化
          return
        }
        
        const workItems = currentProject.workItems
        console.log('工作項數據:', workItems)
        
        // 準備甘特圖數據
        const labels = workItems.map(item => item.name)
        
        // 計算每個工項的計畫時間長度（以天為單位）
        const plannedDurations = workItems.map(item => {
          const start = new Date(formatDate(item.plannedStart))
          const end = new Date(formatDate(item.plannedEnd))
          return Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)))
        })
        
        // 計算每個工項的實際時間長度（以天為單位）
        const actualDurations = workItems.map(item => {
          if (!item.actualStart) return 0
          
          const start = new Date(formatDate(item.actualStart))
          const end = item.actualEnd ? new Date(formatDate(item.actualEnd)) : new Date()
          return Math.ceil((end - start) / (1000 * 60 * 60 * 24))
        })
        
        console.log('準備創建圖表...')
        
        // 創建圖表
        ganttChart.value = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [
              {
                label: '計畫工期',
                data: plannedDurations,
                backgroundColor: 'rgba(54, 162, 235, 0.7)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1,
                borderRadius: 4,
                barPercentage: 0.8
              },
              {
                label: '實際工期',
                data: actualDurations,
                backgroundColor: 'rgba(46, 204, 113, 0.7)',
                borderColor: 'rgba(46, 204, 113, 1)',
                borderWidth: 1,
                borderRadius: 4,
                barPercentage: 0.6
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
                text: `${currentProject.name} - 工程進度甘特圖`,
                font: {
                  size: 16,
                  weight: 'bold'
                }
              },
              legend: {
                position: 'bottom',
                display: true,
                onClick: function(e, legendItem, legend) {
                  const index = legendItem.datasetIndex;
                  const ci = legend.chart;
                  
                  if (ci.isDatasetVisible(index)) {
                    ci.hide(index);
                  } else {
                    ci.show(index);
                  }
                  
                  ci.update();
                },
                labels: {
                  font: {
                    size: 12
                  },
                  padding: 15,
                  usePointStyle: true,
                  pointStyle: 'circle'
                }
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    return context.dataset.label + ': ' + context.raw + ' 天'
                  },
                  footer: function(tooltipItems) {
                    const itemIndex = tooltipItems[0].dataIndex
                    const workItem = workItems[itemIndex]
                    return [
                      `計畫起始: ${formatDate(workItem.plannedStart)}`,
                      `計畫完成: ${formatDate(workItem.plannedEnd)}`,
                      `實際起始: ${workItem.actualStart ? formatDate(workItem.actualStart) : '未開始'}`,
                      `實際完成: ${workItem.actualEnd ? formatDate(workItem.actualEnd) : '進行中'}`,
                      `進度: ${workItem.progress}%`
                    ]
                  }
                }
              },
            },
            scales: {
              x: {
                stacked: false,
                title: {
                  display: true,
                  text: '工作天數'
                }
              },
              y: {
                stacked: false,
                title: {
                  display: true,
                  text: '工項名稱'
                }
              }
            }
          }
        })
        
        chartInitialized.value = true // 標記圖表已初始化
        console.log('甘特圖創建成功')
      } catch (error) {
        console.error('創建甘特圖時發生錯誤:', error)
      }
    }
    
    // 創建水平進度圖
    const createHorizontalChart = () => {
      console.log('開始創建水平進度圖...')
      
      if (!horizontalCanvas.value) {
        console.error('水平進度圖 Canvas 元素不存在')
        return
      }
      
      if (horizontalChart.value) {
        horizontalChart.value.destroy()
        horizontalChart.value = null
      }
      
      nextTick(() => {
        try {
          // 確保 Canvas 元素已經渲染
          if (!horizontalCanvas.value) {
            console.error('水平進度圖 Canvas 元素在 nextTick 中不存在')
            return
          }
          
          const ctx = horizontalCanvas.value.getContext('2d')
          
          if (!ctx) {
            console.error('無法獲取 Canvas 上下文')
            return
          }
          
          console.log('成功獲取 Canvas 上下文')
          
          // 設置 Canvas 尺寸
          if (horizontalCanvas.value.parentElement) {
            const parentWidth = horizontalCanvas.value.parentElement.clientWidth
            const parentHeight = horizontalCanvas.value.parentElement.clientHeight || 350
            
            console.log(`父元素尺寸: ${parentWidth}x${parentHeight}`)
            
            // 使用 style 屬性設置尺寸
            horizontalCanvas.value.style.width = '100%'
            horizontalCanvas.value.style.height = '100%'
            
            // 設置實際像素尺寸
            horizontalCanvas.value.width = parentWidth
            horizontalCanvas.value.height = parentHeight
          }
          
          const currentProject = getCurrentProject()
          if (!currentProject || !currentProject.operationItems) {
            console.error('當前項目或操作項不存在')
            return
          }
          
          const operationItems = currentProject.operationItems
          console.log('操作項數據:', operationItems)
          
          // 準備水平進度圖數據
          const labels = operationItems.map(item => item.name)
          const completionRates = operationItems.map(item => item.completionRate)
          
          console.log('準備創建圖表...')
          
          // 創建進度圖
          horizontalChart.value = new Chart(ctx, {
            type: 'bar',
            data: {
              labels: labels,
              datasets: [
                {
                  label: '完成率',
                  data: completionRates,
                  backgroundColor: 'rgba(46, 204, 113, 0.7)',
                  borderColor: 'rgba(46, 204, 113, 1)',
                  borderWidth: 1,
                  borderRadius: 4,
                  barPercentage: 0.7
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
                  text: `${currentProject.name} - 作業完成率`,
                  font: {
                    size: 16,
                    weight: 'bold'
                  }
                },
                legend: {
                  display: false
                },
                tooltip: {
                  callbacks: {
                    label: function(context) {
                      return '完成率: ' + context.raw + '%'
                    },
                    footer: function(tooltipItems) {
                      const itemIndex = tooltipItems[0].dataIndex
                      const operationItem = operationItems[itemIndex]
                      return [
                        `單位: ${operationItem.unit}`,
                        `預計數量: ${operationItem.plannedQuantity}`,
                        `已完成: ${operationItem.completedQuantity}`,
                        `備註: ${operationItem.notes}`
                      ]
                    }
                  }
                }
              },
              scales: {
                x: {
                  beginAtZero: true,
                  max: 100,
                  title: {
                    display: true,
                    text: '完成率 (%)'
                  }
                },
                y: {
                  title: {
                    display: true,
                    text: '作業項目'
                  }
                }
              }
            }
          })
          
          console.log('水平進度圖創建成功')
        } catch (error) {
          console.error('創建水平進度圖時發生錯誤:', error)
        }
      })
    }
    
    // 處理窗口大小變化
    const handleResize = () => {
      try {
        console.log('處理窗口大小變化...')
        
        // 如果圖表已經初始化，只更新尺寸而不重新創建
        if (chartInitialized.value) {
          if (ganttChart.value && selectedReportType.value === 'gantt') {
            ganttChart.value.resize();
            return;
          }
          
          if (horizontalChart.value && selectedReportType.value === 'horizontal') {
            horizontalChart.value.resize();
            return;
          }
        }
        
        // 立即更新 canvas 尺寸
        if (ganttCanvas.value && ganttCanvas.value.parentElement) {
          const parentWidth = ganttCanvas.value.parentElement.clientWidth
          const parentHeight = ganttCanvas.value.parentElement.clientHeight || 350
          
          ganttCanvas.value.style.width = '100%'
          ganttCanvas.value.style.height = '100%'
          ganttCanvas.value.width = parentWidth
          ganttCanvas.value.height = parentHeight
        }
        
        if (horizontalCanvas.value && horizontalCanvas.value.parentElement) {
          const parentWidth = horizontalCanvas.value.parentElement.clientWidth
          const parentHeight = horizontalCanvas.value.parentElement.clientHeight || 350
          
          horizontalCanvas.value.style.width = '100%'
          horizontalCanvas.value.style.height = '100%'
          horizontalCanvas.value.width = parentWidth
          horizontalCanvas.value.height = parentHeight
        }
      } catch (error) {
        console.error('處理窗口大小變化時發生錯誤:', error)
      }
    }
    
    // 監聽報表類型變化
    watch(selectedReportType, (newValue) => {
      // 重置圖表初始化狀態
      chartInitialized.value = false;
      
      // 清除現有圖表
      if (ganttChart.value) {
        ganttChart.value.destroy();
        ganttChart.value = null;
      }
      
      if (horizontalChart.value) {
        horizontalChart.value.destroy();
        horizontalChart.value = null;
      }
      
      nextTick(() => {
        if (newValue === 'gantt') {
          createGanttChart()
        } else if (newValue === 'horizontal') {
          createHorizontalChart()
        }
      })
    })
    
    // 監聽選擇的專案變化
    watch(selectedProject, () => {
      // 重置圖表初始化狀態
      chartInitialized.value = false;
      
      // 清除現有圖表
      if (ganttChart.value) {
        ganttChart.value.destroy();
        ganttChart.value = null;
      }
      
      if (horizontalChart.value) {
        horizontalChart.value.destroy();
        horizontalChart.value = null;
      }
      
      nextTick(() => {
        if (selectedReportType.value === 'gantt') {
          createGanttChart()
        } else if (selectedReportType.value === 'horizontal') {
          createHorizontalChart()
        }
      })
    })
    
    // 從API獲取專案數據
    const fetchProjects = async () => {
      try {
        // 實際應用中，這裏應該從API獲取數據
        // const response = await axios.get('http://localhost:5000/api/weekly-report')
        // projects.value = response.data
        
        // 目前使用模擬數據
        console.log('使用模擬數據')
        
        // 初始化圖表
        nextTick(() => {
          if (selectedReportType.value === 'gantt') {
            createGanttChart()
          } else if (selectedReportType.value === 'horizontal') {
            createHorizontalChart()
          }
        })
      } catch (error) {
        console.error('獲取週報數據失敗:', error)
      }
    }
    
    onMounted(() => {
      // 延遲初始化，確保DOM已完全渲染
      setTimeout(() => {
        fetchProjects()
        
        if (window.ResizeObserver) {
          resizeObserver.value = new ResizeObserver(() => {
            // 使用防抖處理，避免頻繁觸發
            if (resizeTimeout) clearTimeout(resizeTimeout)
            resizeTimeout = setTimeout(handleResize, 500) // 增加延遲時間
          })
          
          if (ganttCanvas.value && ganttCanvas.value.parentElement) {
            resizeObserver.value.observe(ganttCanvas.value.parentElement)
          }
          
          if (horizontalCanvas.value && horizontalCanvas.value.parentElement) {
            resizeObserver.value.observe(horizontalCanvas.value.parentElement)
          }
        }
        
        window.addEventListener('resize', handleResize)
        
        // 手動觸發一次 resize 事件，確保圖表正確渲染
        // 但不要立即觸發，給予足夠時間讓 DOM 完全渲染
        setTimeout(handleResize, 1000)
      }, 1000) // 增加初始化延遲時間
    })
    
    onBeforeUnmount(() => {
      if (ganttChart.value) {
        ganttChart.value.destroy()
        ganttChart.value = null
      }
      
      if (horizontalChart.value) {
        horizontalChart.value.destroy()
        horizontalChart.value = null
      }
      
      if (resizeObserver.value) {
        resizeObserver.value.disconnect()
      }
      
      window.removeEventListener('resize', handleResize)
    })
    
    return {
      ganttCanvas,
      horizontalCanvas,
      selectedReportType,
      selectedProject,
      projects,
      getCurrentProject,
      formatDate
    }
  }
}
</script>

<style scoped>
.weekly-report-view {
  background-color: var(--card-background);
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
  color: var(--text-color);
  font-size: 1.5rem;
  margin-bottom: 20px;
  text-align: left;
  border-bottom: 2px solid var(--border-color);
  padding-bottom: 10px;
  flex-shrink: 0;
}
.report-controls {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: var(--card-background);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
.filter-group {
  display: flex;
  align-items: center;
  gap: 10px;
}
.filter-group label {
  color: var(--text-color);
  font-weight: 500;
  white-space: nowrap;
}
.filter-group select {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background-color: var(--card-background);
  color: var(--text-color);
  font-size: 0.9rem;
  min-width: 150px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.filter-group select:hover {
  border-color: var(--primary-color);
}
.filter-group select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}
.report-container {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.chart-container {
  flex-grow: 1;
  position: relative;
  min-height: 250px;
  border-radius: 8px;
  overflow: hidden;
  background-color: var(--card-background);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

/* 表格樣式 */
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
  background-color: var(--card-background);
  border-radius: 8px;
  overflow: hidden;
}
table th, td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}
table th {
  background-color: var(--primary-color);
  color: white;
  font-weight: 500;
}
table tr:last-child td {
  border-bottom: none;
}
table tr:hover {
  background-color: rgba(0, 0, 0, 0.02);
}


@media (max-width: 992px) {
  .progress-summary {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .report-controls {
    flex-direction: column;
    align-items: flex-start;
  }
  .filter-group {
    width: 100%;
    margin-right: 0;
    margin-bottom: 10px;
  }
  .filter-group select {
    width: 100%;
  }
  .progress-summary {
    grid-template-columns: 1fr;
  }
  .chart-container {
    height: 300px; /* 小螢幕上減少高度 */
  }
}
</style>