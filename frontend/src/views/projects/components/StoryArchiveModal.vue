<script setup lang="ts">
import { computed } from 'vue'
import { X, User, MapPin } from 'lucide-vue-next'

const props = defineProps<{
    visible: boolean
    project: any
}>()

const emit = defineEmits(['close', 'open-preview'])

const characters = computed(() => props.project?.assets?.characters || [])
const scenes = computed(() => props.project?.assets?.scenes || [])

const handleItemClick = (type: 'character' | 'scene', index: number) => {
    const list = type === 'character' ? characters.value : scenes.value
    emit('open-preview', list, index)
}

// Deterministic random generator
const pseudoRandom = (seed: number) => {
    const x = Math.sin(seed) * 10000;
    return x - Math.floor(x);
}

const getCardStyle = (index: number, total: number) => {
    // Archive Box / Folder System Layout (Multiple Rows)

    // Seed generator
    // const r_seed = pseudoRandom(index * 1337 + 42)
    const y_seed = pseudoRandom(index * 9999 + 777)
    const rot_seed = pseudoRandom(index * 555 + 123)

    // Layout configuration
    const ITEMS_PER_ROW = 6 // Adjust based on container width
    const stepX = 50 // Overlap distance
    const rowHeight = 120 // Vertical distance between rows

    const row = Math.floor(index / ITEMS_PER_ROW)
    const col = index % ITEMS_PER_ROW

    // Calculate row width to center it
    // Items in this row might be less than ITEMS_PER_ROW for the last row
    const itemsInThisRow = Math.min(ITEMS_PER_ROW, total - (row * ITEMS_PER_ROW))
    const rowWidth = (itemsInThisRow - 1) * stepX
    const startX = -rowWidth / 2

    // Base position
    const x = startX + (col * stepX)

    // Vertical position: centered vertically based on total rows
    const totalRows = Math.ceil(total / ITEMS_PER_ROW)
    const totalHeight = (totalRows - 1) * rowHeight
    const startY = -totalHeight / 2
    const baseY = startY + (row * rowHeight)

    // Jitter Y: +/- 10px
    const jitterY = (y_seed * 20) - 10

    // Rotation: Slight tilt (-5 to 5 deg)
    const rotation = (rot_seed * 10) - 5

    return {
        transform: `translate(${x}px, ${baseY + jitterY}px) rotate(${rotation}deg)`,
        zIndex: index + 1
    }
}
</script>

<template>
    <Teleport to="body">
        <transition name="modal-fade">
            <div v-if="visible"
                class="fixed inset-0 z-100 bg-black/60 backdrop-blur-md flex items-center justify-center p-8 perspective-viewport"
                @click="emit('close')">

                <!-- Close Button -->
                <button @click.stop="emit('close')"
                    class="absolute top-6 right-6 p-2 rounded-full hover:bg-white/10 text-white transition-colors z-50">
                    <X class="w-8 h-8" />
                </button>

                <!-- Archive Book Container -->
                <div class="book-container relative w-full max-w-5xl aspect-[1.5/1] flex z-10 select-none shadow-2xl bg-[#2c3e50] p-2 rounded-xl"
                    @click.stop>

                    <!-- Left Page: Characters -->
                    <div
                        class="book-page left-page flex-1 bg-[#fdfbf7] rounded-l-lg relative overflow-hidden flex flex-col p-8 paper-texture shadow-inner origin-right">
                        <!-- Spine Shadow (Left) -->
                        <div class="absolute top-0 right-0 bottom-0 w-24 bg-linear-to-l from-black/20 via-black/5 to-transparent pointer-events-none z-20 mix-blend-multiply"></div>
                        
                        <!-- Header -->
                        <div class="flex flex-col items-center mb-10 shrink-0">
                            <h2
                                class="text-2xl font-serif font-black text-gray-800 tracking-tight flex items-center gap-3">
                                <User class="w-8 h-8 text-blue-500" />
                                角色
                            </h2>
                            <!-- <div class="w-24 h-1 bg-blue-500/30 mt-2 rounded-full"></div> -->
                        </div>

                        <!-- Stacking Area -->
                        <div class="flex-1 relative w-full flex items-center justify-center perspective-area paper-lines">
                            <div v-if="characters.length === 0" class="text-gray-400 font-serif italic text-xl">
                                暂无角色记录
                            </div>

                            <div v-for="(char, idx) in characters" :key="char.id"
                                class="polaroid absolute transition-all duration-300 ease-out cursor-pointer group hover:z-1000!"
                                :style="getCardStyle(idx as number, characters.length)"
                                @click="handleItemClick('character', idx as number)">
                                <!-- Tooltip -->
                                <div
                                    class="absolute -top-12 left-1/2 -translate-x-1/2 bg-black/80 text-white text-xs px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50 shadow-lg">
                                    {{ char.name }}
                                    <div
                                        class="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-black/80 rotate-45">
                                    </div>
                                </div>

                                <!-- Card Content -->
                                <div
                                    class="bg-white p-2 shadow-md border border-gray-200 w-30 h-37.5 flex flex-col items-center transform transition-transform duration-300 group-hover:-translate-y-10 group-hover:scale-110 group-hover:shadow-2xl group-hover:z-100 group-hover:rotate-0">
                                    <!-- Image area square-ish or consistent -->
                                    <div
                                        class="w-26 h-26 bg-gray-100 overflow-hidden mb-2 border border-gray-100 shrink-0">
                                        <img v-if="char.image_url" :src="char.image_url"
                                            class="w-full h-full object-cover" />
                                        <div v-else
                                            class="w-full h-full flex items-center justify-center text-blue-300 font-bold text-2xl bg-blue-50">
                                            {{ char.name[0] }}
                                        </div>
                                    </div>
                                    <div class="text-gray-600 text-[10px] truncate max-w-full px-1 leading-none mt-1 w-full text-center"
                                        :title="char.name">{{ char.name }}</div>
                                </div>
                            </div>
                        </div>
                    </div>


                    <!-- Right Page: Scenes -->
                    <div
                        class="book-page right-page flex-1 bg-[#fdfbf7] rounded-r-lg relative overflow-hidden flex flex-col p-8 paper-texture shadow-lg origin-left">
                        <!-- Spine Shadow (Right) -->
                        <div
                            class="absolute left-0 top-0 bottom-0 w-24 bg-linear-to-r from-black/20 via-black/5 to-transparent pointer-events-none z-20 mix-blend-multiply">
                        </div>

                        <!-- Header -->
                        <div class="flex flex-col items-center mb-10 shrink-0">
                            <h2
                                class="text-2xl font-serif font-black text-gray-800 tracking-tight flex items-center gap-3">
                                <MapPin class="w-8 h-8 text-orange-500" />
                                场景
                            </h2>
                            <div class="w-24 h-1 bg-orange-500/30 mt-2 rounded-full"></div>
                        </div>

                        <!-- Stacking Area -->
                        <div class="flex-1 relative w-full flex items-center justify-center perspective-area paper-lines">
                            <div v-if="scenes.length === 0" class="text-gray-400 font-serif italic text-xl">
                                暂无场景记录
                            </div>
                            <div v-for="(scene, idx) in scenes" :key="scene.id"
                                class="polaroid absolute transition-all duration-300 ease-out cursor-pointer group hover:z-1000!"
                                :style="getCardStyle(idx as number, scenes.length)"
                                @click="handleItemClick('scene', idx as number)">
                                <!-- Tooltip -->
                                <div
                                    class="absolute -top-12 left-1/2 -translate-x-1/2 bg-black/80 text-white text-xs px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none shadow-lg z-2000!">
                                    {{ scene.location_name }}
                                    <div
                                        class="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-black/80 rotate-45">
                                    </div>
                                </div>

                                <!-- Card Content -->
                                <!-- Polaroid 600 dimensions: 3.5 x 4.2 in (~89 x 107 mm). Ratio 1:1.2 -->
                                <div
                                    class="bg-white p-2 shadow-md border border-gray-200 w-30 h-37.5 flex flex-col items-center transform transition-transform duration-300 group-hover:-translate-y-10 group-hover:scale-110 group-hover:shadow-2xl group-hover:z-100 group-hover:rotate-0">
                                    <div
                                        class="w-26 h-26 bg-gray-100 overflow-hidden mb-2 border border-gray-100 shrink-0">
                                        <img v-if="scene.image_url" :src="scene.image_url"
                                            class="w-full h-full object-cover" />
                                        <div v-else
                                            class="w-full h-full flex items-center justify-center text-orange-300 font-bold bg-orange-50">
                                            <MapPin class="w-6 h-6" />
                                        </div>
                                    </div>
                                    <div class="text-gray-600 text-[10px] truncate max-w-full px-1 leading-none mt-1 w-full text-center"
                                        :title="scene.location_name">{{ scene.location_name }}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </transition>
    </Teleport>
</template>

<style scoped>
.paper-texture {
    background-color: #fdfbf7;
    background-image: 
        /* Red Margin Line */
        linear-gradient(90deg, transparent 31px, #fca5a5 32px, transparent 33px),
        /* Subtle Noise */
        url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.03'/%3E%3C/svg%3E");
}

.paper-lines {
    background-image: repeating-linear-gradient(transparent, transparent 29px, #cbd5e1 30px);
}

.font-handwriting {
    font-family: 'Courier New', Courier, monospace;
}

/* Modal Fade */
.modal-fade-enter-active,
.modal-fade-leave-active {
    transition: opacity 0.4s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
    opacity: 0;
}

/* Book Opening Animation */
.perspective-viewport {
    perspective: 2000px;
}

.book-container {
    transform-style: preserve-3d;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.modal-fade-enter-active .book-container {
    animation: zoomInBook 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.modal-fade-enter-active .left-page {
    animation: openBookLeft 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards 0.1s;
    opacity: 0; /* Ensure hidden before animation */
}

.modal-fade-enter-active .right-page {
    animation: openBookRight 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards 0.1s;
    opacity: 0; /* Ensure hidden before animation */
}

@keyframes zoomInBook {
    from {
        transform: scale(0.8) translateY(20px);
        opacity: 0;
    }
    to {
        transform: scale(1) translateY(0);
        opacity: 1;
    }
}

@keyframes openBookLeft {
    0% {
        transform: rotateY(-90deg);
        opacity: 0;
    }
    40% {
        opacity: 1;
    }
    100% {
        transform: rotateY(0deg);
        opacity: 1;
    }
}

@keyframes openBookRight {
    0% {
        transform: rotateY(90deg);
        opacity: 0;
    }
    40% {
        opacity: 1;
    }
    100% {
        transform: rotateY(0deg);
        opacity: 1;
    }
}

.perspective-area {
    perspective: 1000px;
}
</style>
