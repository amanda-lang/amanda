" Vim syntax file
" Language: Amanda
" Maintainer: Sténio Jacinto
" Latest Revision: 01 Feb 2021

if exists("b:current_syntax")
  finish
endif


"Amanda keywords
syn  keyword AmaKeywords mostra retorna
syn  keyword AmaKeywords verdadeiro falso retorna converte
syn  keyword AmaKeywords se senao entao enquanto
syn  keyword AmaKeywords para faca de  func
syn  keyword AmaKeywords fim classe 
syn  keyword AmaKeywords inclua como super

"Amanda Literals
syn match AmaNumber '\d\+'
syn match AmaNumber '\d\+\.\d*'
syn match AmaNumber '[-+]\d\+'
syn match AmaNumber '[-+]\d\+\.\d*'
syn match AmaString '".*"'
syn match AmaString "'.*'"
syn keyword AmaBuiltins verdadeiro falso nulo


"Comment
syn match AmaComment "#.*$"

"Identifier
syn match AmaIdentifier "\h\+"

"Types
syn keyword AmaTypes int real bool texto vazio 



let b:current_syntax = "ama"

hi def link AmaComment     Comment
hi def link AmaKeywords    Keyword
hi def link AmaTypes       Type
hi def link AmaString      String
hi def link AmaNumber      Constant
hi def link AmaBuiltins    Constant
