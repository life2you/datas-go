package storage

import (
	"container/heap"
	"sync"

	"github.com/life2you/datas-go/logger"
)

// 区块队列
var GlobalBlockQueue *PriorityQueue

// 交易队列
var GlobalTransactionQueue *PriorityQueue

func InitQueue() {
	// 区块队列
	GlobalBlockQueue = NewPriorityQueue("区块队列")
	// 交易队列
	GlobalTransactionQueue = NewPriorityQueue("交易队列")
}

// Item 是存储在优先队列中的元素
type Item struct {
	Value    interface{} // 元素的值，可以使用任何类型
	Priority int64       // 元素的优先级，数值越小优先级越高
	index    int         // 堆中元素的索引，由 container/heap 维护
}

// priorityQueueImpl 实现了 container/heap.Interface 接口
// 这是优先队列底层使用的数据结构（最小堆）
type priorityQueueImpl []*Item

func (pq priorityQueueImpl) Len() int { return len(pq) }

// Less 用于比较两个元素的优先级
// 我们希望数值越小优先级越高，所以这里比较的是优先级数值
func (pq priorityQueueImpl) Less(i, j int) bool {
	return pq[i].Priority < pq[j].Priority
}

// Swap 交换两个元素，并更新它们的索引
func (pq priorityQueueImpl) Swap(i, j int) {
	pq[i], pq[j] = pq[j], pq[i]
	pq[i].index = i
	pq[j].index = j
}

// Push 将一个元素添加到堆中 (由 heap.Push 调用)
func (pq *priorityQueueImpl) Push(x any) {
	n := len(*pq)
	item := x.(*Item)
	item.index = n // 设置新元素的索引
	*pq = append(*pq, item)
}

// Pop 从堆中移除并返回优先级最高的元素 (由 heap.Pop 调用)
func (pq *priorityQueueImpl) Pop() any {
	old := *pq
	n := len(old)
	item := old[n-1]   // 获取最后一个元素
	old[n-1] = nil     // 避免内存泄漏
	item.index = -1    // 表示元素已经不在堆中
	*pq = old[0 : n-1] // 截断 slice
	return item        // 返回的是被移除的元素 (原堆顶元素)
}

// PriorityQueue 是线程安全的优先队列
type PriorityQueue struct {
	heap      *priorityQueueImpl // 底层堆实现
	mu        sync.Mutex         // 用于同步访问堆的互斥锁
	QueueName string             // 队列名称
}

// NewPriorityQueue 创建一个新的线程安全的优先队列
func NewPriorityQueue(queueName string) *PriorityQueue {
	pqImpl := &priorityQueueImpl{}
	heap.Init(pqImpl) // 初始化堆
	return &PriorityQueue{
		heap:      pqImpl,
		QueueName: queueName,
	}
}

// Push 将一个值及其优先级推入队列
func (pq *PriorityQueue) Push(value interface{}, priority int64) {
	pq.mu.Lock()
	defer pq.mu.Unlock()

	item := &Item{
		Value:    value,
		Priority: priority,
	}
	// heap.Push 会调用 pq.heap 的 Push 方法并调整堆结构
	heap.Push(pq.heap, item)
}

// Pop 移除并返回优先级最高的元素。
// 如果队列为空，返回 nil, 0, false。
func (pq *PriorityQueue) Pop() (interface{}, int64, bool) {
	pq.mu.Lock()
	defer pq.mu.Unlock()

	if pq.heap.Len() == 0 {
		return nil, 0, false // 队列为空
	}

	// heap.Pop 会调用 pq.heap 的 Pop 方法并调整堆结构
	item := heap.Pop(pq.heap).(*Item)
	logger.Infof("队列 %s 移除元素 %d ", pq.QueueName, item.Priority)
	return item.Value, item.Priority, true
}

// Peek 查看优先级最高的元素，但不从队列中移除。
// 如果队列为空，返回 nil, 0, false。
func (pq *PriorityQueue) Peek() (interface{}, int64, bool) {
	pq.mu.Lock()
	defer pq.mu.Unlock()

	if pq.heap.Len() == 0 {
		return nil, 0, false // 队列为空
	}

	item := (*pq.heap)[0] // 直接访问堆顶元素 (索引 0)
	return item.Value, item.Priority, true
}

// Len 返回队列中元素的数量
func (pq *PriorityQueue) Len() int {
	pq.mu.Lock()
	defer pq.mu.Unlock()
	return pq.heap.Len()
}

// IsEmpty 检查队列是否为空
func (pq *PriorityQueue) IsEmpty() bool {
	return pq.Len() == 0 // Len 方法内部已加锁
}
