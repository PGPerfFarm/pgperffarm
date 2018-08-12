import React        from 'react';

import echarts from 'echarts/lib/echarts';
// import  'echarts/lib/chart/line';
import 'echarts/lib/component/tooltip'
import 'echarts/lib/component/grid'
import 'echarts/lib/chart/bar'

import 'echarts/lib/component/title';

// import { pieOption, barOption, lineOption, scatterOption, mapOption, radarOption, candlestickOption } from './optionConfig/options'
// const BarReact = asyncComponent(() => import(/* webpackChunkName: "BarReact" */'./EchartsDemo/BarReact')) // bar component


// General rate bar
class RateBar extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            std: 150000,
            curMark: 143732,
        }
    }

    componentDidMount() {
        let std = this.props.std;
        let curMark = this.props.curMark;

        // init echarts
        let myChart = echarts.init(this.refs.waterall);
        let colorList = [
            '#C33531','#EFE42A','#64BD3D','#EE9201','#29AAE3',
            '#B74AE5','#0AAF9F','#E89589'
        ];
        let option = {
            tooltip : {
                trigger: 'axis',
                axisPointer : {
                    type : 'shadow'
                }
            },
            legend: {
                data: ['std', 'current']
            },
            grid: {
                left: '2%',
                right: '0%',
                bottom: '20%',
                top: '-20%',
                containLabel: false
            },
            xAxis:  {
                type: 'value',
                show: false,
                splitLine:{
                    show: false
                },
            },
            yAxis: {
                type: 'category',
                show: false,
                // splitLine:{
                //     show: false
                // },
                data: ['2 clients']
            },
            series: [
                {
                    itemStyle:{
                        normal:{
                            color:'#0050b3'
                        }
                    },
                    name: 'std',
                    type: 'bar',
                    stack: 'current',
                    label: {
                        normal: {
                            show: true,
                            position: 'insideRight'
                        }
                    },
                    data: [std]
                },
                {
                    itemStyle:{
                        normal:{
                            color:'#13c2c2'
                        }
                    },
                    name: 'curMark',
                    type: 'bar',
                    stack: 'current',
                    label: {
                        normal: {
                            show: true,
                            position: 'insideRight'
                        }
                    },
                    data: [curMark]
                },
            ]
        };

        myChart.setOption(option);
    }

    render() {
        return (
            <div ref="waterall" className="rate-bar" style={{ width: 240, height: 30 }}></div>
        );
    }
}

export default RateBar;