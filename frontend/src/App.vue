<template>
  <div id="app">
    <header class="app-header">
      <h1>建設公司戰情室</h1>
      <div class="header-controls">
        <div class="date-display">{{ currentDate }}</div>
      </div>
    </header>
    
    <div class="dashboard-container">
      <div class="progress-section">
        <ProgressDashboard />
      </div>
      
      <div class="chart-section">
        <ChartView />
      </div>
      
      <div class="gantt-section">
        <ProjectGanttChart />
      </div>
      
      <div class="map-section">
        <MapView />
      </div>
      
      <!-- 添加週報元件 -->
      <div class="weekly-report-section">
        <WeeklyReport />
      </div>
    </div>
  </div>
</template>

<script>
import ProgressDashboard from './components/ProgressDashboard.vue'
import ChartView from './components/ChartView.vue'
import MapView from './components/MapView.vue'
import ProjectGanttChart from './components/ProjectGanttChart.vue'
import { ref, onMounted } from 'vue'
import WeeklyReport from './components/WeeklyReport.vue'

export default {
  name: 'App',
  components: {
    ProgressDashboard,
    ChartView,
    MapView,
    ProjectGanttChart,
    WeeklyReport  // 添加 WeeklyReport 組件
  },
  setup() {
    const currentDate = ref('')
    
    const updateDate = () => {
      const now = new Date()
      const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric', 
        weekday: 'long',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }
      currentDate.value = now.toLocaleDateString('zh-TW', options)
    }
    
    onMounted(() => {
      updateDate()
      setInterval(updateDate, 1000)
    })
    
    return {
      currentDate
    }
  }
}
</script>

<style>
:root {
  --primary-color: #3498db;
  --secondary-color: #2ecc71;
  --background-color: #f5f7fa;
  --card-background: #ffffff;
  --text-color: #333333;
  --border-color: #dddddd;
  --success-color: #2ecc71;
  --warning-color: #f39c12;
  --danger-color: #e74c3c;
}
* {
  box-sizing: border-box;
}
body {
  margin: 0;
  padding: 0;
  font-family: 'Microsoft JhengHei', Arial, sans-serif;
  background-color: var(--background-color);
  color: var(--text-color);
  overflow-y: auto;
}

#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding: 0;
  overflow-x: hidden;
}

.app-header {
  background-color: var(--primary-color);
  color: white;
  padding: 15px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 600;
}

.header-controls {
  display: flex;
  align-items: center;
}

.date-display {
  background-color: rgba(255, 255, 255, 0.1);
  padding: 8px 15px;
  border-radius: 4px;
  font-size: 0.9rem;
}

.dashboard-container {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  grid-template-areas: 
    "progress progress progress progress progress progress progress progress progress progress progress progress"
    "chart chart chart chart chart chart gantt gantt gantt gantt gantt gantt"
    "map map map map map map map map map map map map"
    "weekly weekly weekly weekly weekly weekly weekly weekly weekly weekly weekly weekly";
  gap: 20px;
  padding: 20px;
  width: 100%;
  max-width: 1800px;
  margin: 0 auto;
  min-height: calc(100vh - 80px);
  height: auto;
}

.progress-section {
  grid-area: progress;
  min-height: 450px; /* 增加高度 */
  height: auto;
  max-height: 600px; /* 設置最大高度 */
}

.chart-section {
  grid-area: chart;
  min-height: 500px;
}

.gantt-section {
  grid-area: gantt;
  min-height: 500px;
}

.map-section {
  grid-area: map;
  min-height: 500px;
}

.weekly-report-section {
  grid-area: weekly;
  min-height: 500px;
  display: block; /* 確保顯示 */
}

/* 大螢幕 (1200px 以上) */
@media (min-width: 1201px) {
  .dashboard-container {
    grid-template-areas: 
      "progress progress progress progress progress progress progress progress progress progress progress progress"
      "chart chart chart chart chart chart gantt gantt gantt gantt gantt gantt"
      "map map map map map map map map map map map map"
      "weekly weekly weekly weekly weekly weekly weekly weekly weekly weekly weekly weekly";
  }
  
  .progress-section {
    min-height: 500px; /* 大螢幕增加更多高度 */
  }
}

/* 中等螢幕 (768px - 1200px) */
@media (min-width: 768px) and (max-width: 1200px) {
  .dashboard-container {
    grid-template-areas: 
      "progress progress progress progress progress progress progress progress progress progress progress progress"
      "chart chart chart chart chart chart chart chart chart chart chart chart"
      "gantt gantt gantt gantt gantt gantt gantt gantt gantt gantt gantt gantt"
      "map map map map map map map map map map map map"
      "weekly weekly weekly weekly weekly weekly weekly weekly weekly weekly weekly weekly";
    gap: 15px;
    padding: 15px;
  }
}

/* 小螢幕 (768px 以下) */
@media (max-width: 767px) {
  .dashboard-container {
    grid-template-columns: 1fr;
    grid-template-areas: 
      "progress"
      "chart"
      "gantt"
      "map"
      "weekly";
    gap: 10px;
    padding: 10px;
  }
  
  .app-header {
    padding: 10px 15px;
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-controls {
    margin-top: 10px;
    width: 100%;
  }
  
  .date-display {
    width: 100%;
    text-align: center;
  }
  
  .progress-section,
  .chart-section,
  .gantt-section,
  .map-section {
    grid-column: 1;
    margin-bottom: 10px;
    min-height: auto;
  }
}
</style>
