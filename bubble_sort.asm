# MIPS Bubble Sort
# This program will store 5 values into memory and sort them in ascending order.
# The array starts at memory address 0x1000

.data
array: .word 5, 2, 9, 1, 6
length: .word 5

.text
.globl main
main:
    # 1. Initialize Array addresses from the .data segment
    la   $a0, array          # $a0 = Array base address
    lw   $a1, length         # $a1 = array length (5)
    
    # Outer loop index i in $t2
    add  $t2, $zero, $zero

outer_loop:
    # Exit condition: i >= length - 1
    addi $t3, $a1, -1          # $t3 = length - 1
    slt  $t9, $t2, $t3         # $t9 = (i < length - 1)
    beq  $t9, $zero, exit_sort # If i >= length - 1, we are done sorting
    
    # Inner loop index j in $t4
    add  $t4, $zero, $zero
    
    # Inner loop bound = length - i - 1 -> store in $t5
    sub  $t5, $a1, $t2
    addi $t5, $t5, -1
    
inner_loop:
    slt  $t9, $t4, $t5   # $t9 = (j < length - i - 1)
    beq  $t9, $zero, next_outer 
    
    # Load array[j]
    sll  $t6, $t4, 2     # $t6 = j * 4 (byte offset)
    add  $t6, $a0, $t6   # $t6 = exact address of array[j]
    lw   $t7, 0($t6)     # $t7 = array[j]
    
    # Load array[j+1]
    lw   $t8, 4($t6)     # $t8 = array[j+1]
    
    # Compare
    slt  $t9, $t8, $t7   # $t9 = (array[j+1] < array[j])
    beq  $t9, $zero, next_inner# if array[j+1] >= array[j], elements are in order, skip swap
    
    # Swap
    sw   $t8, 0($t6)
    sw   $t7, 4($t6)
    
next_inner:
    addi $t4, $t4, 1     # j++
    j    inner_loop
    
next_outer:
    addi $t2, $t2, 1     # i++
    j    outer_loop
    
exit_sort:
    # Set syscall number for exit (10)
    addi $v0, $zero, 10
    syscall
