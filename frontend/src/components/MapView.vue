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
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

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
      if (mapContainer.value) {
        // 修復圖示問題
        delete L.Icon.Default.prototype._getIconUrl
        L.Icon.Default.mergeOptions({
          iconUrl: markerIcon,
          iconRetinaUrl: markerIcon2x,
          shadowUrl: markerShadow,
          iconSize: [25, 41],
          iconAnchor: [12, 41],
          popupAnchor: [1, -34],
          tooltipAnchor: [16, -28],
          shadowSize: [41, 41]
        })

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
  background-color: var(--card-background);
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  padding: 20px;
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  overflow: auto;
}

.map-container {
  position: relative;
  width: 100%;
  flex-grow: 1;
  min-height: 250px;
  max-height: calc(100vh - 350px);
  overflow: hidden;
  border-radius: 8px;
  box-sizing: border-box;
  margin-bottom: 20px;
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

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.search-input-wrapper input {
  width: 100%;
  padding: 8px 12px;
  padding-right: 70px; /* 增加右側填充，為按鈕留出空間 */
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.search-btn {
  position: absolute;
  right: 0;
  top: 0;
  height: 100%;
  width: auto; /* 設置為自動寬度 */
  max-width: 70px; /* 限制最大寬度 */
  padding: 0 12px;
  background-color: var(--primary-color);
  border: none;
  border-top-right-radius: 6px;
  border-bottom-right-radius: 6px;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden; /* 防止內容溢出 */
}

.search-btn i {
  font-size: 0.9rem;
  white-space: nowrap;
}

/* 專案摘要樣式更新 */
.project-summary {
  margin-top: 0;
  padding: 15px;
  background-color: var(--card-background);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
  min-height: 120px;
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

/* 修改地圖搜尋框位置

我將修改 MapView.vue 的樣式，讓搜尋框在大螢幕上顯示在專案類型的右邊，而在小螢幕上保持在專案類型下方。這樣可以更妥善地利用畫面空間。
*/
.map-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: var(--card-background);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  justify-content: space-between; /* 讓元素分散對齊 */
  align-items: center;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 0 0 auto; /* 不要伸縮，保持原始大小 */
}

.search-group {
  display: flex;
  flex: 0 1 300px; /* 可以收縮，但最大寬度為300px */
  max-width: 300px; /* 限制最大寬度 */
}

@media (max-width: 768px) {
  .map-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }
  
  .filter-group, .search-group {
    width: 100%;
    max-width: none;
    flex: 1 1 auto;
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
