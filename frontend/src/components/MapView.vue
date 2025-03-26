<template>
  <div class="map-view">
    <h2 class="dashboard-title">工程地理分佈</h2>
    
    <div class="map-controls">
      <div class="filter-group">
        <label for="project-filter">專案類型:</label>
        <select id="project-filter" v-model="selectedFilter" @change="filterProjects">
          <option value="all">全部專案</option>
          <option value="active">進行中</option>
          <option value="completed">已完成</option>
          <option value="planned">規劃中</option>
        </select>
      </div>
      
      <div class="search-group">
        <div class="search-input-wrapper">
          <input 
            type="text" 
            placeholder="搜尋專案..." 
            v-model="searchQuery"
            @input="debounceSearch"
          >
          <button class="search-btn" @click="searchProjects">
            <i class="fas fa-search">搜尋</i>
          </button>
        </div>
      </div>
    </div>
    
    <div class="map-container" ref="mapContainer"></div>
    
    <div class="project-summary">
      <h3>專案分佈摘要</h3>
      <div class="summary-stats">
        <div class="stat-item">
          <div class="stat-value">{{ projectStats.north }}</div>
          <div class="stat-label">北部</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ projectStats.central }}</div>
          <div class="stat-label">中部</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ projectStats.south }}</div>
          <div class="stat-label">南部</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ projectStats.east }}</div>
          <div class="stat-label">東部</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

export default {
  name: 'MapView',
  setup() {
    const mapContainer = ref(null)
    const map = ref(null)
    const markers = ref([])
    const selectedFilter = ref('all')
    const searchQuery = ref('')
    const isSearching = ref(false)
    const searchTimeout = ref(null)
    
    const projectStats = ref({
      north: 8,
      central: 6,
      south: 5,
      east: 3
    })
    
    // 模擬專案資料
    const allProjects = ref([
      { id: 1, name: '台北商辦大樓', lat: 25.033, lng: 121.565, status: 'active', type: '商業建築' },
      { id: 2, name: '新竹科技園區', lat: 24.815, lng: 120.967, status: 'active', type: '工業建築' },
      { id: 3, name: '台中住宅社區', lat: 24.147, lng: 120.673, status: 'completed', type: '住宅建築' },
      { id: 4, name: '高雄港口擴建', lat: 22.618, lng: 120.267, status: 'active', type: '基礎建設' },
      { id: 5, name: '花蓮觀光飯店', lat: 23.991, lng: 121.601, status: 'planned', type: '商業建築' }
    ])
    
    // 過濾後的專案
    const projects = ref([...allProjects.value])
    
    // 防抖搜尋函數
    const debounceSearch = () => {
      if (searchTimeout.value) {
        clearTimeout(searchTimeout.value)
      }
      
      searchTimeout.value = setTimeout(() => {
        searchProjects()
      }, 300)
    }
    
    // 搜尋專案
    const searchProjects = () => {
      if (isSearching.value) return
      
      isSearching.value = true
      
      try {
        // 重置專案列表
        if (!searchQuery.value.trim() && selectedFilter.value === 'all') {
          projects.value = [...allProjects.value]
        } else {
          const query = searchQuery.value.toLowerCase().trim()
          
          projects.value = allProjects.value.filter(project => {
            const matchesSearch = !query || 
              project.name.toLowerCase().includes(query) || 
              project.type.toLowerCase().includes(query)
              
            const matchesFilter = selectedFilter.value === 'all' || 
              project.status === selectedFilter.value
              
            return matchesSearch && matchesFilter
          })
        }
        
        // 更新地圖標記
        addProjectMarkers()
      } finally {
        isSearching.value = false
      }
    }
    
    // 過濾專案
    const filterProjects = () => {
      searchProjects()
    }
    
    // 初始化地圖
    const initMap = () => {
      // 初始化地圖，中心設在台灣中部
      if (mapContainer.value) {
        map.value = L.map(mapContainer.value).setView([23.97, 120.97], 8)
        
        // 添加地圖圖層
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map.value)
        
        // 添加專案標記
        addProjectMarkers()
      }
    }
    
    // 添加專案標記
    const addProjectMarkers = () => {
      // 清除現有標記
      markers.value.forEach(marker => {
        if (map.value) {
          map.value.removeLayer(marker)
        }
      })
      markers.value = []
      
      // 添加新標記
      projects.value.forEach(project => {
        if (map.value) {
          const marker = L.marker([project.lat, project.lng]).addTo(map.value)
          
          // 創建彈出視窗內容
          const popupContent = `
            <div class="popup-content">
              <h3>${project.name}</h3>
              <p><strong>類型:</strong> ${project.type}</p>
              <p><strong>狀態:</strong> ${getStatusText(project.status)}</p>
              <button class="popup-btn">查看詳情</button>
            </div>
          `
          
          marker.bindPopup(popupContent)
          markers.value.push(marker)
        }
      })
    }
    
    const getStatusText = (status) => {
      switch(status) {
        case 'active': return '進行中'
        case 'completed': return '已完成'
        case 'planned': return '規劃中'
        default: return status
      }
    }
    
    // 監聽篩選條件變化
    watch(selectedFilter, () => {
      if (map.value) {
        addProjectMarkers()
      }
    })
    
    onMounted(() => {
      // 確保 DOM 已經渲染完成
      setTimeout(() => {
        initMap()
      }, 100)
    })
    
    // 監聽搜尋條件變化
    watch(selectedFilter, () => {
      searchProjects()
    })
    
    return {
      mapContainer,
      selectedFilter,
      searchQuery,
      projectStats,
      debounceSearch,
      searchProjects,
      filterProjects
    }
  }
}
</script>

<style scoped>
.map-view {
  background-color: #ffffff;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  padding: 20px;
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  overflow: auto; /* 改為 auto，允許內容超出時滾動 */
}

.map-container {
  position: relative;
  width: 100%;
  flex-grow: 1;
  min-height: 250px;
  max-height: calc(100vh - 350px); /* 限制地圖最大高度 */
  overflow: hidden;
  border-radius: 8px;
  box-sizing: border-box;
  margin-bottom: 20px; /* 增加與摘要區域的間距 */
}

/* 專案摘要樣式更新 */
.project-summary {
  margin-top: 0; /* 修改頂部間距 */
  padding: 15px;
  background-color: var(--card-background, #f8f9fa);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  flex-shrink: 0; /* 防止摘要區域被壓縮 */
  min-height: 120px; /* 確保摘要區域有最小高度 */
}

.project-summary h3 {
  margin: 0 0 15px 0;
  color: var(--text-color);
  font-size: 1.1rem;
  font-weight: 600;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 15px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--primary-color);
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.9rem;
  color: var(--text-color);
}

/* 更新彈出視窗樣式 */
:deep(.leaflet-popup-content-wrapper) {
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

:deep(.popup-content) {
  padding: 15px;
}

:deep(.popup-content h3) {
  font-size: 1.1rem;
  color: var(--text-color);
  margin-bottom: 12px;
}

:deep(.popup-content p) {
  margin: 8px 0;
  color: #666;
}

:deep(.popup-btn) {
  width: 100%;
  padding: 8px 16px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 12px;
}

:deep(.popup-btn:hover) {
  background-color: #2980b9;
  transform: translateY(-1px);
}

/* 響應式設計 */
@media (max-width: 768px) {
  .map-controls {
    flex-direction: column;
    gap: 15px;
  }
  
  .filter-group, .search-group {
    width: 100%;
    max-width: none;
  }
  
  .summary-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .map-container {
    max-height: 50vh; /* 在手機上調整地圖高度 */
  }
}

@media (min-width: 1200px) {
  .map-container {
    max-height: calc(100vh - 400px); /* 在大螢幕上進一步限制地圖高度 */
  }
}
</style>
