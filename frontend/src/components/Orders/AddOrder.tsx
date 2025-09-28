import {
  Button,
  DialogActionTrigger,
  DialogTitle,
  Input,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FiTrendingUp } from "react-icons/fi"

import { type OrderCreate, OrdersService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTrigger,
} from "../ui/dialog"
import { Field } from "../ui/field"

const AddOrder = () => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isValid, isSubmitting },
  } = useForm<OrderCreate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      symbol: "",
      amount: 0,
    },
  })

  const mutation = useMutation({
    mutationFn: (data: OrderCreate) =>
      OrdersService.createOrder({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Trading order placed successfully.")
      reset()
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] })
    },
  })

  const onSubmit: SubmitHandler<OrderCreate> = (data) => {
    mutation.mutate(data)
  }

  return (
    <DialogRoot
      size={{ base: "xs", md: "md" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
    >
      <DialogTrigger asChild>
        <Button value="add-order" my={4} colorPalette="green">
          <FiTrendingUp fontSize="16px" />
          Place Order
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Place Trading Order</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Enter the stock symbol and investment amount.</Text>
            <VStack gap={4}>
              <Field
                required
                invalid={!!errors.symbol}
                errorText={errors.symbol?.message}
                label="Stock Symbol"
                helperText="e.g., AAPL, TSLA, MSFT"
              >
                <Input
                  {...register("symbol", {
                    required: "Stock symbol is required.",
                    pattern: {
                      value: /^[A-Z]+$/,
                      message: "Symbol must be uppercase letters only.",
                    },
                  })}
                  placeholder="AAPL"
                  type="text"
                  style={{ textTransform: "uppercase" }}
                />
              </Field>

              <Field
                required
                invalid={!!errors.amount}
                errorText={errors.amount?.message}
                label="Investment Amount"
                helperText="Dollar amount to invest"
              >
                <Input
                  {...register("amount", {
                    required: "Investment amount is required.",
                    min: {
                      value: 1,
                      message: "Amount must be at least $1.",
                    },
                    valueAsNumber: true,
                  })}
                  placeholder="100.00"
                  type="number"
                  step="0.01"
                />
              </Field>
            </VStack>
          </DialogBody>

          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button
                variant="subtle"
                colorPalette="gray"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            </DialogActionTrigger>
            <Button
              variant="solid"
              colorPalette="green"
              type="submit"
              disabled={!isValid}
              loading={isSubmitting}
            >
              Place Order
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default AddOrder