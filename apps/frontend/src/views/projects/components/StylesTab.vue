<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { styleApi } from '@/api'
import { Trash2, Image as ImageIcon, Plus, Upload } from 'lucide-vue-next'
import NeuButton from '@/components/base/NeuButton.vue'
import { useMessage } from '@/utils/useMessage'
import { useConfirm } from '@/utils/useConfirm'
import { startOnboardingTour } from '@/utils/tour'
import defaultImg from '@/assets/default.png'

const message = useMessage()
const confirmDialog = useConfirm()
const { t } = useI18n()
const styles = ref<any[]>([])
const loading = ref(false)

// Create Mode
const isCreating = ref(false)
const form = reactive({ name: '', file: null as File | null })
const previewUrl = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

const fetchStyles = async () => {
  loading.value = true
  try {
    const res: any = await styleApi.list()
    // Add random rotation and subtle position offset for "scattered polaroid" look
    styles.value = res.map((s: any) => ({
        ...s,
        rotation: (Math.random() * 6 - 3).toFixed(1), // -3 to +3 degrees
        offsetY: (Math.random() * 10 - 5).toFixed(1) // -5px to 5px
    }))
  } catch (e) {
    message.error(t('projects.styles.messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

const processImage = async (file: File): Promise<File> => {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const reader = new FileReader()
    
    reader.onload = (e) => {
      img.src = e.target?.result as string
    }
    
    img.onload = () => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      if (!ctx) return reject(new Error('Canvas context not available'))
      
      const size = Math.min(img.width, img.height)
      canvas.width = size
      canvas.height = size
      
      const offsetX = (img.width - size) / 2
      const offsetY = (img.height - size) / 2
      
      ctx.drawImage(img, offsetX, offsetY, size, size, 0, 0, size, size)
      
      canvas.toBlob((blob) => {
        if (!blob) return reject(new Error('Image processing failed'))
        
        const maxSizeBytes = 1024 * 1024
        if (blob.size <= maxSizeBytes) {
          const processedFile = new File([blob], file.name, { type: 'image/png' })
          resolve(processedFile)
        } else {
          let quality = 0.9
          const compress = () => {
            canvas.toBlob((compressedBlob) => {
              if (!compressedBlob) return reject(new Error('Compression failed'))
              
              if (compressedBlob.size <= maxSizeBytes || quality <= 0.1) {
                const processedFile = new File([compressedBlob], file.name, { type: 'image/jpeg' })
                resolve(processedFile)
              } else {
                quality -= 0.1
                compress()
              }
            }, 'image/jpeg', quality)
          }
          compress()
        }
      }, 'image/png')
    }
    
    img.onerror = () => reject(new Error('Image loading failed'))
    reader.readAsDataURL(file)
  })
}

const handleFileChange = async (e: Event) => {
    const target = e.target as HTMLInputElement
    if (target.files && target.files[0]) {
        const file = target.files[0]
        try {
            const processedFile = await processImage(file)
            form.file = processedFile
            previewUrl.value = URL.createObjectURL(processedFile)
            
            const sizeMB = (processedFile.size / (1024 * 1024)).toFixed(2)
            message.info(t('projects.styles.messages.imageProcessed', { size: sizeMB }))
        } catch (error) {
            message.error(t('projects.styles.messages.imageProcessFailed'))
            console.error(error)
        }
    }
}

const triggerUpload = () => {
    fileInput.value?.click()
}

const saveStyle = async () => {
  if (!form.name || !form.file) return message.warning(t('projects.styles.messages.missingForm'))
  
  const formData = new FormData()
  formData.append('name', form.name)
  formData.append('file', form.file)

  try {
    await styleApi.create(formData)
    message.success(t('projects.styles.messages.saved'))
    resetForm()
    fetchStyles()
  } catch (e) {
    message.error(t('projects.styles.messages.saveFailed'))
  }
}

const resetForm = () => {
    isCreating.value = false
    form.name = ''
    form.file = null
    previewUrl.value = ''
    if (fileInput.value) fileInput.value.value = ''
}

const deleteStyle = async (id: number) => {
  if (!await confirmDialog.show(t('projects.styles.messages.deleteConfirmText'), t('projects.styles.messages.deleteConfirmTitle'))) return
  
  try {
    await styleApi.delete(id)
    message.success(t('projects.styles.messages.deleted'))
    fetchStyles()
  } catch (e) { message.error(t('projects.styles.messages.deleteFailed')) }
}

// const handleConfirmCreate = async (data: any) => {
//     // data is { name, file } from the modal
//     form.name = data.name
//     form.file = data.file
//     await saveStyle()
// }

const handlePaste = async (e: ClipboardEvent) => {
    if (!isCreating.value) return
    
    const items = e.clipboardData?.items
    if (!items) return

    for (const item of items) {
        if (item.type.indexOf('image') !== -1) {
            const file = item.getAsFile()
            if (file) {
                try {
                    const processedFile = await processImage(file)
                    form.file = processedFile
                    previewUrl.value = URL.createObjectURL(processedFile)
                    
                    const sizeMB = (processedFile.size / (1024 * 1024)).toFixed(2)
                    message.info(t('projects.styles.messages.imagePasted', { size: sizeMB }))
                } catch (error) {
                    message.error(t('projects.styles.messages.pasteFailed'))
                    console.error(error)
                }
                break
            }
        }
    }
}

onMounted(() => {
    fetchStyles()
    window.addEventListener('paste', handlePaste)

    startOnboardingTour('styles_view', [
        {
            element: '#tour-styles-create-btn',
            theme: 'blue',
            image: defaultImg,
            popover: { title: t('projects.styles.tour.createTitle'), description: t('projects.styles.tour.createDesc'), side: 'left' }
        },
        {
            element: '#tour-styles-grid',
            theme: 'yellow',
            popover: { title: t('projects.styles.tour.libraryTitle'), description: t('projects.styles.tour.libraryDesc'), side: 'top' }
        }
    ])
})

onUnmounted(() => {
    window.removeEventListener('paste', handlePaste)
})
</script>

<template>
  <div class="h-full p-10 flex flex-col">
    <div class="flex items-center justify-between mb-2">
      <h2 class="text-3xl font-black text-gray-800 font-serif">{{ t('projects.styles.title') }}</h2>
      <NeuButton v-if="!isCreating" size="sm" @click="isCreating = true" id="tour-styles-create-btn">
        <Plus class="w-4 h-4 mr-2" /> {{ t('projects.styles.newStyle') }}
      </NeuButton>
    </div>
    <p class="text-gray-500 italic font-serif mb-8">{{ t('projects.styles.subtitle') }}</p>

    <transition name="fade">
        <div v-if="isCreating" class="absolute inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm" @click.self="resetForm">
           <!-- New Style Modal (Polaroid Style) -->
           <div class="relative w-96 bg-[#fdfbf7] p-4 shadow-2xl transform rotate-1 border border-gray-200 paper-texture pb-12 transition-all duration-300">
             <!-- Tape -->
             <div class="absolute -top-3 left-1/2 -translate-x-1/2 w-32 h-8 bg-yellow-200/80 shadow-sm transform -rotate-2 z-20"></div>
             
             <!-- Close Button -->
             <!-- <button @click="resetForm" class="absolute top-2 right-2 text-gray-400 hover:text-red-500 transition-colors z-20">
               <Trash2 class="w-5 h-5" />
             </button> -->

             <!-- Content -->
             <div class="bg-gray-100 aspect-square w-full mb-4 relative overflow-hidden group cursor-pointer border border-gray-200" @click="triggerUpload">
                <img v-if="previewUrl" :src="previewUrl" class="w-full h-full object-cover" />
                <div v-else class="w-full h-full flex flex-col items-center justify-center text-gray-400 gap-2 hover:bg-gray-200 transition-colors">
                    <Upload class="w-8 h-8" />
                    <span class="text-xs font-bold uppercase tracking-widest">{{ t('projects.styles.clickToUpload') }}</span>
                </div>
                <input ref="fileInput" type="file" class="hidden" accept="image/*" @change="handleFileChange" />
             </div>

             <div class="relative">
                 <input 
                    v-model="form.name" 
                    type="text" 
                    :placeholder="t('projects.styles.namePlaceholder')" 
                    class="w-full text-center font-handwriting text-2xl text-gray-700 bg-transparent border-b border-transparent focus:border-gray-300 outline-none placeholder-gray-300 pb-2"
                    autofocus
                 />
                 <!-- <div class="absolute right-0 bottom-2 text-gray-300 pointer-events-none">
                    <ImageIcon class="w-4 h-4" />
                 </div> -->
             </div>

             <!-- Action Button (Hidden but triggered via Enter or Click) -->
             <div class="absolute bottom-4 right-4 left-4 flex justify-center">
                 <button 
                    @click="saveStyle"
                    :disabled="!form.name || !form.file"
                    class="w-full py-2 bg-gray-800 text-white font-bold text-xs uppercase tracking-widest hover:bg-black transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
                 >
                    {{ t('projects.styles.save') }}
                 </button>
             </div>
           </div>
        </div>
    </transition>

    <!-- Grid Layout for Styles -->
    <div class="flex-1 overflow-y-auto custom-scroll pr-4 -mr-4 pt-4" id="tour-styles-grid">
      <div class="grid grid-cols-[repeat(auto-fill,minmax(180px,1fr))] gap-x-6 gap-y-12 p-8">
          <div 
            v-for="style in styles"
            :key="style.id"
            class="polaroid-card group relative transition-all duration-300 select-none"
            :style="{ 
                transform: `rotate(${style.rotation}deg) translateY(${style.offsetY}px)`,
            }"
          >
             <!-- Polaroid Inner -->
             <div class="bg-white p-2 pb-8 shadow-md group-hover:shadow-2xl group-hover:scale-110 transition-all duration-500 ease-out border border-gray-200/50 relative z-10">
                <!-- Image Aspect Ratio -->
                <div class="aspect-square bg-gray-900 relative overflow-hidden mb-2 shadow-inner">
                    <img :src="style.image_url" class="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity duration-500" />
                    <div class="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                </div>

                <div class="flex items-center justify-center px-1 relative">
                    <h3 class="font-handwriting text-xl text-gray-700 truncate max-w-[140px] text-center" :title="style.name">{{ style.name }}</h3>
                    
                    <button 
                        @click.stop="deleteStyle(style.id)" 
                        class="absolute -right-1 top-0 text-gray-300 hover:text-red-500 transition-all opacity-0 group-hover:opacity-100 scale-75 group-hover:scale-100"
                    >
                        <Trash2 class="w-4 h-4" />
                    </button>
                </div>
             </div>

             <!-- Tape Effect (Randomized) -->
             <div class="absolute -top-3 left-1/2 w-20 h-6 bg-yellow-200/80 backdrop-blur-sm border border-yellow-300/60 shadow-sm opacity-80 z-20 pointer-events-none transform" :style="{ transform: `rotate(${(Math.random() * 10 - 5).toFixed(1)}deg) translateX(-50%)` }"></div>
          </div>

          <!-- Empty State -->
          <div v-if="styles.length === 0 && !isCreating" class="col-span-full text-center py-12 text-gray-400">
            <ImageIcon class="w-12 h-12 mx-auto mb-4 opacity-20" />
            <p>{{ t('projects.styles.empty') }}</p>
          </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@700&display=swap');

.font-handwriting {
    font-family: 'Caveat', cursive, sans-serif;
}

.paper-texture {
  background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z' fill='%239C92AC' fill-opacity='0.05' fill-rule='evenodd'/%3E%3C/svg%3E");
}

.fade-enter-active, .fade-leave-active { transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: scale(0.9) translateY(-20px) rotate(-5deg); }

.polaroid-card:hover {
    z-index: 50 !important;
    transform: rotate(0deg) scale(1.15) !important; 
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}
</style>
