import { defineStore } from 'pinia'
import { fetchExamCategories } from '@/api/services/examCategory'

export const useExamCategoryStore = defineStore('examCategory', {
  state: () => ({
    categoryOptions: [],
    selectedCategoryId: '',
    loading: false,
  }),
  actions: {
    async loadCategories() {
      this.loading = true

      try {
        this.categoryOptions = await fetchExamCategories()
      } catch (error) {
        this.categoryOptions = []
      } finally {
        this.loading = false
      }
    },
    bootstrapDefaults() {
      this.categoryOptions = [
        { id: 'english', name: '英语' },
        { id: 'computer', name: '计算机' },
        { id: 'math', name: '高等数学' },
      ]
      this.selectedCategoryId = this.categoryOptions[0]?.id || ''
    },
    setSelectedCategory(categoryId) {
      this.selectedCategoryId = categoryId
    },
  },
})
