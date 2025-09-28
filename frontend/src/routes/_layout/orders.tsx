import {
  Badge,
  Button,
  Container,
  EmptyState,
  Flex,
  Heading,
  Table,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { FiRefreshCw, FiTrash2, FiTrendingUp } from "react-icons/fi"

import { OrdersService } from "@/client"
import AddOrder from "@/components/Orders/AddOrder"
import PendingItems from "@/components/Pending/PendingItems"
import { toaster } from "@/components/ui/toaster"

export const Route = createFileRoute("/_layout/orders")({
  component: Orders,
})

function OrdersTable() {
  const queryClient = useQueryClient()
  const [syncingOrderId, setSyncingOrderId] = useState<number | null>(null)
  const [deletingOrderId, setDeletingOrderId] = useState<number | null>(null)

  const { data, isLoading } = useQuery({
    queryFn: () => OrdersService.listOrders(),
    queryKey: ["orders"],
  })

  const deleteOrderMutation = useMutation({
    mutationFn: (orderId: number) => OrdersService.deleteOrder({ id: orderId }),
    onMutate: (orderId) => {
      setDeletingOrderId(orderId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] })
      setDeletingOrderId(null)
      toaster.create({
        title: "Order deleted successfully",
        type: "success",
      })
    },
    onError: (error: any) => {
      setDeletingOrderId(null)
      const errorMessage = error?.status === 404
        ? "Order not found."
        : "Failed to delete order. Please try again."

      toaster.create({
        title: "Delete failed",
        description: errorMessage,
        type: "error",
      })
    },
  })

  const syncOrderMutation = useMutation({
    mutationFn: (orderId: number) => OrdersService.syncOrder({ id: orderId }),
    onMutate: (orderId) => {
      setSyncingOrderId(orderId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] })
      setSyncingOrderId(null)
      toaster.create({
        title: "Order synchronized successfully",
        type: "success",
      })
    },
    onError: (error: any) => {
      setSyncingOrderId(null)
      const errorMessage = error?.status === 500
        ? "Internal server error during synchronization. Please try again later."
        : error?.status === 404
        ? "Order not found."
        : "Failed to synchronize order. Please try again."

      toaster.create({
        title: "Sync failed",
        description: errorMessage,
        type: "error",
      })
    },
  })

  const orders = data ?? []

  if (isLoading) {
    return <PendingItems />
  }

  if (orders.length === 0) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Indicator>
            <FiTrendingUp />
          </EmptyState.Indicator>
          <VStack textAlign="center">
            <EmptyState.Title>No trading orders yet</EmptyState.Title>
            <EmptyState.Description>
              Your stock trading orders will appear here once placed
            </EmptyState.Description>
          </VStack>
        </EmptyState.Content>
      </EmptyState.Root>
    )
  }

  const getOrderStatusBadge = (order: any) => {
    if (order.buy_filled_qty && order.sell_filled_qty) {
      return <Badge colorPalette="green">Completed</Badge>
    }
    if (order.buy_filled_qty && !order.sell_filled_qty) {
      return <Badge colorPalette="blue">Buy Filled</Badge>
    }
    if (order.alpaca_buy_order_id) {
      return <Badge colorPalette="yellow">Active</Badge>
    }
    return <Badge colorPalette="gray">Pending</Badge>
  }

  return (
    <Table.Root size={{ base: "sm", md: "md" }}>
      <Table.Header>
        <Table.Row>
          <Table.ColumnHeader>Symbol</Table.ColumnHeader>
          <Table.ColumnHeader>Amount ($)</Table.ColumnHeader>
          <Table.ColumnHeader>Quantity</Table.ColumnHeader>
          <Table.ColumnHeader>Buy Price</Table.ColumnHeader>
          <Table.ColumnHeader>Sell Price</Table.ColumnHeader>
          <Table.ColumnHeader>Status</Table.ColumnHeader>
          <Table.ColumnHeader>Force Sell At</Table.ColumnHeader>
          <Table.ColumnHeader>Actions</Table.ColumnHeader>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {orders?.map((order) => (
          <Table.Row key={order.id}>
            <Table.Cell>
              <Text fontWeight="bold" color="blue.500">
                {order.symbol}
              </Text>
            </Table.Cell>
            <Table.Cell>
              <Text>${order.amount.toFixed(2)}</Text>
            </Table.Cell>
            <Table.Cell>
              {order.quantity || order.buy_filled_qty || "—"}
            </Table.Cell>
            <Table.Cell>
              {order.buy_filled_avg_price ? (
                <Text color="green.500">
                  ${order.buy_filled_avg_price.toFixed(2)}
                </Text>
              ) : (
                "—"
              )}
            </Table.Cell>
            <Table.Cell>
              {order.sell_filled_avg_price ? (
                <Text color="red.500">
                  ${order.sell_filled_avg_price.toFixed(2)}
                </Text>
              ) : (
                "—"
              )}
            </Table.Cell>
            <Table.Cell>{getOrderStatusBadge(order)}</Table.Cell>
            <Table.Cell>
              {order.force_sell_at ? (
                <Text fontSize="sm" color="gray.600">
                  {new Date(order.force_sell_at).toLocaleDateString()}
                </Text>
              ) : (
                "—"
              )}
            </Table.Cell>
            <Table.Cell>
              <Flex gap={2}>
                <Button
                  size="sm"
                  variant="ghost"
                  colorPalette="blue"
                  loading={syncingOrderId === order.id}
                  onClick={() => syncOrderMutation.mutate(order.id)}
                >
                  <FiRefreshCw />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  colorPalette="red"
                  loading={deletingOrderId === order.id}
                  onClick={() => deleteOrderMutation.mutate(order.id)}
                >
                  <FiTrash2 />
                </Button>
              </Flex>
            </Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table.Root>
  )
}

function Orders() {
  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        Trading Orders
      </Heading>
      <Text color="gray.600" mb={4}>
        Monitor your stock trading orders and their execution status
      </Text>
      <AddOrder />
      <OrdersTable />
    </Container>
  )
}