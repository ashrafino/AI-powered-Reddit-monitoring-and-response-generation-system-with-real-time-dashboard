/**
 * Cross-browser clipboard utilities with fallback support
 */

export interface ClipboardResult {
  success: boolean
  method: 'modern' | 'legacy' | 'failed'
  error?: string
}

/**
 * Copy text to clipboard with cross-browser compatibility
 * Supports modern Clipboard API with fallback to legacy methods
 */
export async function copyToClipboard(text: string): Promise<ClipboardResult> {
  // Check if we're in a secure context and have modern clipboard API
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text)
      return { success: true, method: 'modern' }
    } catch (error) {
      console.warn('Modern clipboard API failed, falling back to legacy method:', error)
      // Fall through to legacy method
    }
  }

  // Legacy fallback method
  try {
    const textArea = document.createElement('textarea')
    textArea.value = text
    
    // Make the textarea invisible but still focusable
    textArea.style.position = 'fixed'
    textArea.style.left = '-999999px'
    textArea.style.top = '-999999px'
    textArea.style.opacity = '0'
    textArea.style.pointerEvents = 'none'
    textArea.setAttribute('readonly', '')
    textArea.setAttribute('aria-hidden', 'true')
    
    document.body.appendChild(textArea)
    
    // Focus and select the text
    textArea.focus()
    textArea.select()
    textArea.setSelectionRange(0, text.length)
    
    // Execute copy command
    const successful = document.execCommand('copy')
    
    // Clean up
    document.body.removeChild(textArea)
    
    if (successful) {
      return { success: true, method: 'legacy' }
    } else {
      return { 
        success: false, 
        method: 'failed', 
        error: 'execCommand copy returned false' 
      }
    }
  } catch (error) {
    return { 
      success: false, 
      method: 'failed', 
      error: error instanceof Error ? error.message : 'Unknown error' 
    }
  }
}

/**
 * Check if clipboard functionality is available
 */
export function isClipboardSupported(): boolean {
  return !!(navigator.clipboard || document.execCommand)
}

/**
 * Get clipboard capabilities information
 */
export function getClipboardCapabilities(): {
  hasModernAPI: boolean
  hasLegacyAPI: boolean
  isSecureContext: boolean
  userAgent: string
} {
  return {
    hasModernAPI: !!(navigator.clipboard && window.isSecureContext),
    hasLegacyAPI: !!document.execCommand,
    isSecureContext: window.isSecureContext,
    userAgent: navigator.userAgent
  }
}

/**
 * Test clipboard functionality
 */
export async function testClipboard(): Promise<{
  modern: ClipboardResult | null
  legacy: ClipboardResult | null
  capabilities: ReturnType<typeof getClipboardCapabilities>
}> {
  const testText = 'clipboard-test-' + Date.now()
  const capabilities = getClipboardCapabilities()
  
  let modernResult: ClipboardResult | null = null
  let legacyResult: ClipboardResult | null = null
  
  // Test modern API if available
  if (capabilities.hasModernAPI) {
    try {
      await navigator.clipboard.writeText(testText)
      modernResult = { success: true, method: 'modern' }
    } catch (error) {
      modernResult = { 
        success: false, 
        method: 'failed', 
        error: error instanceof Error ? error.message : 'Unknown error' 
      }
    }
  }
  
  // Test legacy API if available
  if (capabilities.hasLegacyAPI) {
    try {
      const textArea = document.createElement('textarea')
      textArea.value = testText
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      
      const successful = document.execCommand('copy')
      document.body.removeChild(textArea)
      
      legacyResult = { 
        success: successful, 
        method: successful ? 'legacy' : 'failed',
        error: successful ? undefined : 'execCommand copy failed'
      }
    } catch (error) {
      legacyResult = { 
        success: false, 
        method: 'failed', 
        error: error instanceof Error ? error.message : 'Unknown error' 
      }
    }
  }
  
  return {
    modern: modernResult,
    legacy: legacyResult,
    capabilities
  }
}