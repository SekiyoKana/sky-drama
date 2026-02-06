import { ref, type Ref } from 'vue'
import { useEventListener } from '@vueuse/core'

/**
 * Returns coordinates of the caret at a specific position in a textarea
 */
function getCaretCoordinates(element: HTMLTextAreaElement, position: number) {
    const div = document.createElement('div')
    const style = window.getComputedStyle(element)
    
    // Copy font/text styles
    const properties = [
        'direction', 'boxSizing', 'width', 'height', 'overflowX', 'overflowY',
        'borderTopWidth', 'borderRightWidth', 'borderBottomWidth', 'borderLeftWidth', 'borderStyle',
        'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft',
        'fontStyle', 'fontVariant', 'fontWeight', 'fontStretch', 'fontSize', 'fontSizeAdjust', 'lineHeight', 'fontFamily',
        'textAlign', 'textTransform', 'textIndent', 'textDecoration',
        'letterSpacing', 'wordSpacing', 'tabSize', 'MozTabSize', 'whiteSpace', 'wordBreak', 'wordWrap'
    ]

    properties.forEach(prop => {
        div.style.setProperty(prop.replace(/[A-Z]/g, m => '-' + m.toLowerCase()), style.getPropertyValue(prop.replace(/[A-Z]/g, m => '-' + m.toLowerCase())))
    })

    div.style.position = 'absolute'
    div.style.top = '0px'
    div.style.left = '0px'
    div.style.visibility = 'hidden'
    div.style.whiteSpace = 'pre-wrap'
    div.style.wordWrap = 'break-word'
    
    // IMPORTANT: Replicate the textarea's content box width exactly
    // 1. clientWidth excludes scrollbars
    // 2. We use border-box to include padding in width, but we REMOVE borders from the div
    //    so that div width = (content + padding) = textarea clientWidth
    div.style.boxSizing = 'border-box'
    div.style.width = `${element.clientWidth}px`
    div.style.borderWidth = '0px'
    div.style.margin = '0px'
    div.style.overflow = 'hidden'

    div.textContent = element.value.substring(0, position)
    
    const span = document.createElement('span')
    span.textContent = element.value.substring(position) || '.'
    div.appendChild(span)
    
    document.body.appendChild(div)
    
    // span.offsetLeft is relative to the div (which has 0 border)
    const spanLeft = span.offsetLeft
    const spanTop = span.offsetTop
    
    document.body.removeChild(div)
    
    const elementRect = element.getBoundingClientRect()
    
    // Calculate absolute position
    // elementRect.left is the outside border edge
    // content starts at left + borderLeft
    const borderLeft = parseFloat(style.borderLeftWidth) || 0
    const borderTop = parseFloat(style.borderTopWidth) || 0
    
    const absoluteX = elementRect.left + borderLeft + spanLeft - element.scrollLeft
    const absoluteY = elementRect.top + borderTop + spanTop - element.scrollTop

    return {
        left: absoluteX,
        top: absoluteY,
        height: parseInt(style.lineHeight) || 20
    }
}

export function useMention(textareaRef: Ref<HTMLTextAreaElement | null>) {
    const isMentionVisible = ref(false)
    const mentionX = ref(0)
    const mentionY = ref(0)
    const mentionQuery = ref('')
    const mentionStartIndex = ref(-1)

    const updatePosition = () => {
        if (!isMentionVisible.value || !textareaRef.value || mentionStartIndex.value === -1) return
        
        const coords = getCaretCoordinates(textareaRef.value, mentionStartIndex.value + 1)
        mentionX.value = coords.left
        // Return TOP of the line to allow upward positioning
        mentionY.value = coords.top
    }

    useEventListener(window, 'resize', updatePosition)
    useEventListener(window, 'scroll', updatePosition, { capture: true })

    const handleInput = (e: Event) => {
        const target = e.target as HTMLTextAreaElement
        const val = target.value
        const cursorPos = target.selectionStart

        const textBeforeCursor = val.substring(0, cursorPos)
        const lastAt = textBeforeCursor.lastIndexOf('@')
        
        if (lastAt !== -1) {
            const query = textBeforeCursor.substring(lastAt + 1)
            if (!/[\n\r]/.test(query)) {
                mentionStartIndex.value = lastAt
                mentionQuery.value = query
                
                isMentionVisible.value = true
                updatePosition()
                return
            }
        }
        
        isMentionVisible.value = false
    }

    const closeMention = () => {
        isMentionVisible.value = false
    }

    return {
        isMentionVisible,
        mentionX,
        mentionY,
        mentionQuery,
        mentionStartIndex,
        handleInput,
        closeMention,
        updatePosition
    }
}
