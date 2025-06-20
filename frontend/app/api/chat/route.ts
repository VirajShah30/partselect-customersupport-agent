import { NextResponse } from "next/server"

// Allow streaming responses up to 30 seconds
export const maxDuration = 30

export async function POST(req: Request) {
  const { messages } = await req.json()

  // Get the latest user message
  const latestMessage = messages[messages.length - 1]

  if (latestMessage?.role === "user") {
    try {
      // Call your backend API
      const backendResponse = await fetch("http://localhost:5001/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: latestMessage.content,
        }),
      })

      if (backendResponse.ok) {
        const backendData = await backendResponse.json()
        console.log("Backend response:", backendData)

        // Extract the response text from your backend format
        let responseText = ""
        if (typeof backendData === "string") {
          responseText = backendData
        } else if (backendData.response) {
          responseText = backendData.response
        } else if (backendData.message) {
          responseText = backendData.message
        } else {
          responseText = JSON.stringify(backendData, null, 2)
        }

        // Return the backend response as the assistant message
        return NextResponse.json({
          id: Date.now().toString(),
          role: "assistant",
          content: responseText,
        })
      } else {
        console.error("Backend API error:", backendResponse.status)
        return NextResponse.json({
          id: Date.now().toString(),
          role: "assistant",
          content:
            "Sorry, I'm having trouble connecting to our parts database right now. Please try again in a moment.",
        })
      }
    } catch (error) {
      console.error("Failed to call backend API:", error)
      return NextResponse.json({
        id: Date.now().toString(),
        role: "assistant",
        content: "Sorry, I'm having trouble connecting to our parts database right now. Please try again in a moment.",
      })
    }
  }

  // Fallback response if no user message
  return NextResponse.json({
    id: Date.now().toString(),
    role: "assistant",
    content: "How can I help you with your appliance parts today?",
  })
}
