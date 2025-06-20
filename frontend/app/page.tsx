"use client"

import type React from "react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Trash2, ArrowUp } from "lucide-react"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
}

export default function PartSelectChatbot() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: [...messages, userMessage],
        }),
      })

      if (response.ok) {
        const assistantMessage = await response.json()
        setMessages((prev) => [...prev, assistantMessage])
      } else {
        const errorMessage: Message = {
          id: Date.now().toString(),
          role: "assistant",
          content: "Sorry, something went wrong. Please try again.",
        }
        setMessages((prev) => [...prev, errorMessage])
      }
    } catch (error) {
      console.error("Error:", error)
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: "Sorry, something went wrong. Please try again.",
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const clearChat = () => {
    setMessages([])
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <img
                src="/ps-25-year-logo.svg"
                alt="PartSelect - Here to help since 1999 - 25 years"
                className="h-12 w-auto"
              />
            </div>
            <div className="text-right">
              <div className="text-xl font-bold text-gray-800">1-888-741-7748</div>
              <div className="text-sm text-gray-800">Monday to Saturday</div>
              <div className="text-sm text-gray-800">8am - 9pm EST</div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6">
        <Card className="min-h-[600px] flex flex-col">
          <CardContent className="flex-1 p-6">
            {messages.length === 0 && (
              <div className="space-y-6">
                <div className="flex items-center space-x-2">
                  
                  <h1 className="text-2xl font-bold text-gray-900">Welcome to PartSelect Customer support!</h1>
                </div>

                <div className="space-y-4 text-gray-700">
                  <p>How can I assit you today?.</p>

                  <div>
                    <p className="font-semibold mb-3">You can ask me questions like:</p>
                    <ul className="space-y-2 ml-4 text-gray-600">
                      <li>• "How can I install part number PS11752778?"</li>
                      <li>• "Is this part compatible with my WDT780SAEM1 model?"</li>
                      <li>• "The ice maker on my Whirlpool fridge is not working. How can I fix it?"</li>
                    </ul>
                  </div>

                 
                </div>
              </div>
            )}

            {messages.length > 0 && (
              <div className="space-y-4">
                {messages.map((message) => (
                  <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`max-w-[80%] rounded-lg px-4 py-3 ${
                        message.role === "user" ? "bg-white border border-gray-200 text-gray-900" : "text-white"
                      }`}
                      style={message.role === "assistant" ? { backgroundColor: "#2f7879" } : {}}
                    >
                      <div className="whitespace-pre-wrap">{message.content}</div>
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-gray-200 rounded-lg px-4 py-3 max-w-[80%]">
                      <div className="flex items-center space-x-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                          <div
                            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                            style={{ animationDelay: "0.1s" }}
                          ></div>
                          <div
                            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                            style={{ animationDelay: "0.2s" }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-500">Thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>

          {/* Input Form */}
          <div className="border-t bg-gray-50 p-4">
            <form onSubmit={handleSubmit} className="flex space-x-2">
              <div className="flex-1 relative">
                <Input
                  value={input}
                  onChange={handleInputChange}
                  placeholder="Ask about refrigerator or dishwasher parts..."
                  className="pr-20 bg-white"
                  disabled={isLoading}
                />
                <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex space-x-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={clearChat}
                    className="h-8 w-8 p-0"
                    disabled={messages.length === 0}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                  <Button
                    type="submit"
                    variant="ghost"
                    size="sm"
                    disabled={isLoading || !input.trim()}
                    className="h-8 w-8 p-0"
                  >
                    <ArrowUp className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </form>
            <div className="text-xs text-gray-500 mt-2 italic">
            Please refer to product links for the most accurate information.
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
