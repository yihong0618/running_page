import React, { useState,useRef ,useEffect  } from 'react';
import styles from './style.module.css';

// 元数据
const measuredData = {
  measuredDataMap: {},
  lastMeasuredItemIndex: -1,
};

const estimatedHeight = (defaultEstimatedItemSize = 50, itemCount) => {
  let measuredHeight = 0;
  const { measuredDataMap, lastMeasuredItemIndex } = measuredData;
  // 计算已经获取过真实高度的项的高度之和
  if (lastMeasuredItemIndex >= 0) {
    const lastMeasuredItem = measuredDataMap[lastMeasuredItemIndex];
    measuredHeight = lastMeasuredItem.offset + lastMeasuredItem.size;
  }
  // 未计算过真实高度的项数
  const unMeasuredItemsCount = itemCount - measuredData.lastMeasuredItemIndex - 1;
  // 预测总高度
  const totalEstimatedHeight = measuredHeight + unMeasuredItemsCount * defaultEstimatedItemSize;
  return totalEstimatedHeight;
}

const getItemMetaData = (props, index) => {
  const { itemSize, itemEstimatedSize = 50 } = props;
  const { measuredDataMap, lastMeasuredItemIndex } = measuredData;
  // 如果当前索引比已记录的索引要大，说明要计算当前索引的项的size和offset
  if (index > lastMeasuredItemIndex) {
    let offset = 0;
    // 计算当前能计算出来的最大offset值
    if (lastMeasuredItemIndex >= 0) {
      const lastMeasuredItem = measuredDataMap[lastMeasuredItemIndex];
      offset += lastMeasuredItem.offset + lastMeasuredItem.size;
    }
    // 计算直到index为止，所有未计算过的项
    for (let i = lastMeasuredItemIndex + 1; i <= index; i++) {
      const currentItemSize = itemSize ? itemSize(i) : itemEstimatedSize;
      measuredDataMap[i] = { size: currentItemSize, offset };
      offset += currentItemSize;
    }
    // 更新已计算的项的索引值
    measuredData.lastMeasuredItemIndex = index;
  }
  return measuredDataMap[index];
};

const getStartIndex = (props, scrollOffset) => {
  const { itemCount } = props;
  let index = 0;
  while (true) {
    const currentOffset = getItemMetaData(props, index).offset;
    if (currentOffset >= scrollOffset) return index;
    if (index >= itemCount) return itemCount;
    index++
  }
}

const getEndIndex = (props, startIndex) => {
  const { height, itemCount } = props;
  // 获取可视区内开始的项
  const startItem = getItemMetaData(props, startIndex);
  // 可视区内最大的offset值
  const maxOffset = startItem.offset + height;
  // 开始项的下一项的offset，之后不断累加此offset，知道等于或超过最大offset，就是找到结束索引了
  let offset = startItem.offset + startItem.size;
  // 结束索引
  let endIndex = startIndex;
  // 累加offset
  while (offset <= maxOffset && endIndex < (itemCount - 1)) {
    endIndex++;
    const currentItem = getItemMetaData(props, endIndex);
    offset += currentItem.size;
  }
  return endIndex;
};

const getRangeToRender = (props, scrollOffset) => {
  const { itemCount } = props;
  const startIndex = getStartIndex(props, scrollOffset);
  const endIndex = getEndIndex(props, startIndex);
  return [
    Math.max(0, startIndex - 2),
    Math.min(itemCount - 1, endIndex + 2),
    startIndex,
    endIndex,
  ];
};

const ListItem = React.memo(({ index, style, ComponentType, onSizeChange, className }) => {
  const domRef = useRef(null);
  
  useEffect(() => {
    if (!domRef.current) return;
    
    const resizeObserver = new ResizeObserver(() => {
      onSizeChange(index, domRef.current);
    });
    
    resizeObserver.observe(domRef.current);
    
    return () => {
      resizeObserver.disconnect();
    };
  }, [index, onSizeChange]);

  // 检查 ComponentType 是否有效
  let content;
  if (React.isValidElement(ComponentType)) {
    // 如果已经是 React 元素
    content = ComponentType;
  } else if (typeof ComponentType === 'function') {
    // 如果是组件函数/类
    // console.log('ComponentType', ComponentType);
    
    content = <ComponentType index={index} />;
  } else {
    // 回退方案
    content = <div>Item {index}</div>;
  }

  return (
    <div style={style} ref={domRef} className={className}>
      {content}
    </div>
  );
});

const VariableSizeList = (props) => {
  const { height, width, itemCount, itemEstimatedSize = 50, children: Child } = props;
  const [scrollOffset, setScrollOffset] = useState(0);
  const [, setState] = useState({});

  const containerStyle = {
    position: 'relative',
    width,
    height,
    overflow: 'auto',
    willChange: 'transform'
  };

  const contentStyle = {
    // height: estimatedHeight(itemEstimatedSize, itemCount),
    width: '100%',
  };

  const sizeChangeHandle = (index, domNode) => {
    debugger
    const height = domNode?.offsetHeight;
    const { measuredDataMap, lastMeasuredItemIndex } = measuredData;
    const itemMetaData = measuredDataMap[index];
    itemMetaData.size = height;
    let offset = 0;
    for (let i = 0; i <= lastMeasuredItemIndex; i++) {
      const itemMetaData = measuredDataMap[i];
      itemMetaData.offset = offset;
      offset += itemMetaData.size;
    }
    setState({});
  }
    
  const getCurrentChildren = () => {
    // TODO:1.这里一直在渲染
    // 2.min,max计算是有问题
    // console.log('Child',Child);
    // debugger
    const [startIndex, endIndex] = getRangeToRender(props, scrollOffset)
    // debugger
    // console.log('123getCurrentChildren', startIndex, endIndex);
    
    const items = [];
    for (let i = startIndex; i <= endIndex; i++) {
      const item = getItemMetaData(props, i);
      const itemStyle = {
        position: 'absolute',
        // height: item.size,
        // width: '100%',
        display:'flex',
        top: item?.offset,
      };
      items.push(
        <ListItem className={styles.listItem} key={i} index={i} style={itemStyle} ComponentType={Child} onSizeChange={sizeChangeHandle} />
      );
    }
    return items;
    // return null
  }

  const scrollHandle = (event) => {
    const { scrollTop } = event.currentTarget;
    setScrollOffset(scrollTop);
  }

  return (
    <div style={containerStyle} onScroll={scrollHandle} >
      <div style={contentStyle} className={styles.content}>
        {getCurrentChildren()}
      </div>
    </div>
  );
};

export default VariableSizeList;

