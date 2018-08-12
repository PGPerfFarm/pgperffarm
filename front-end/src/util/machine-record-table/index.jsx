import React from 'react';
import {Link}     from 'react-router-dom';
import {Icon, Table, Label, Message, Button} from 'semantic-ui-react'
import Pagination from 'util/pagination/index.jsx'
import PGConstant from 'util/constant.jsx'
import './index.css';

function Bubble(props) {

    if (props.num <= 0) {
        return null;
    }
    let className = props.name + 'IconClassName';
    return (
        <Label circular size="mini" className={"mini-label " + className}>
            {props.num}
        </Label>
    );
}

// general basic table
class MachineRecordTable extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            isFirstLoading: true,
            total: this.props.total,
            currentPage: 1,
        }
    }

    onPageNumChange(current) {
        let _this = this
        this.setState({
            currentPage: current
        }, () => {
            _this.props.loadfunc(current);
        });
        console.log('current:' + this.state.currentPage)
    }

    render() {
        // let branch = record.pg_info.pg_branch;
        let _list = this.props.list || []
        let style = {
            display: 'show'
        };
        let listBody = _list.map((record, index) => {
            let machine = record.machine_info;
            let system = machine.os_name + ' ' + machine.os_version + ' ' + machine.comp_name + ' ' + machine.comp_version;
            let alias = machine.alias;


            let trend = record.trend
            let improvedIconClassName = trend.improved > 0 ? 'improved' : 'anonymous'
            let quoIconClassName = trend.quo > 0 ? 'quo' : 'anonymous'
            let regressiveIconClassName = trend.regressive > 0 ? 'regressive' : 'anonymous'
            return (

                <Table.Row key={index}>
                    {/*alias*/}
                    <Table.Cell>
                        <Link color='linkedin' to={'machineInfo/' + machine.machine_sn}>
                            {alias}
                        </Link>
                    </Table.Cell>

                    {/*system*/}
                    {/*<Table.Cell><a href="#">{system}</a></Table.Cell>*/}

                    {/*branch*/}
                    {/*<Table.Cell>{branch}</Table.Cell>*/}

                    {/*trending-data*/}

                    <Table.Cell textAlign='center'>
                        <Icon className={"bgc-clear " + improvedIconClassName} name='smile outline' size='large'/>
                        <Bubble num={trend.improved} name="improved"/>
                    </Table.Cell>
                    <Table.Cell textAlign='center'>
                        <Icon className={"bgc-clear " + quoIconClassName} name='meh outline' size='large'/>
                        <Bubble num={trend.quo} name="quo"/>
                    </Table.Cell>
                    <Table.Cell textAlign='center'>
                        <Icon className={"bgc-clear " + regressiveIconClassName} name='frown outline'
                              size='large'/>
                        <Bubble num={trend.regressive} name="regressive"/>
                    </Table.Cell>


                    <Table.Cell textAlign='center'>
                        <Link color='linkedin' to={'/detailInfo/' + record.uuid}>
                            <Icon name='linkify'/> Link
                        </Link>
                    </Table.Cell>

                    {/*commit*/}
                    <Table.Cell><a target="_blank" href={ PGConstant.PG_GITHUB_MIRROR + record.commit}>{ record.commit.substring(0, 7)}</a></Table.Cell>

                    {/*date*/}
                    <Table.Cell>{record.add_time}</Table.Cell>
                </Table.Row>
            );
        });

        return (
            <Table  basic='very' selectable structured compact textAlign='center'>
                <Table.Header celled>
                    {/*<Table.Row>*/}
                    {/*<Table.HeaderCell rowSpan='9'>Branch: 10_STABLE</Table.HeaderCell>*/}
                    {/*</Table.Row>*/}
                    <Table.Row>
                        <Table.HeaderCell rowSpan='2'>Alias</Table.HeaderCell>
                        {/*<Table.HeaderCell rowSpan='2'>System</Table.HeaderCell>*/}
                        {/*<Table.HeaderCell rowSpan='2'>Branch</Table.HeaderCell>*/}
                        <Table.HeaderCell colSpan='3'>Trending</Table.HeaderCell>
                        <Table.HeaderCell rowSpan='2'>Detail</Table.HeaderCell>
                        <Table.HeaderCell rowSpan='2'>Commit</Table.HeaderCell>
                        <Table.HeaderCell rowSpan='2'>Date</Table.HeaderCell>
                    </Table.Row>
                    <Table.Row>
                        <Table.HeaderCell>improvement</Table.HeaderCell>
                        <Table.HeaderCell>status quo</Table.HeaderCell>
                        <Table.HeaderCell>regression</Table.HeaderCell>
                    </Table.Row>

                </Table.Header>

                <Table.Body>
                    {listBody}
                </Table.Body>
                <Table.Footer>
                    <Table.Row>
                        <Table.HeaderCell colSpan='10'>
                            {/*<Menu size='small' floated='right' pagination>*/}
                            {/*<Menu.Item as='a' icon>*/}
                            {/*<Icon name='chevron left'/>*/}
                            {/*</Menu.Item>*/}
                            {/*<Menu.Item as='a'>1</Menu.Item>*/}
                            {/*<Menu.Item as='a'>2</Menu.Item>*/}
                            {/*<Menu.Item as='a'>3</Menu.Item>*/}
                            {/*<Menu.Item as='a'>4</Menu.Item>*/}
                            {/*<Menu.Item as='a' icon>*/}
                            {/*<Icon name='chevron right'/>*/}
                            {/*</Menu.Item>*/}
                            {/*</Menu>*/}
                            <Pagination style={style} onChange={(current) => this.onPageNumChange(current)} pageSize={20}
                                        current={this.state.currentPage} total={this.props.total}/>

                        </Table.HeaderCell>

                    </Table.Row>
                </Table.Footer>
            </Table>
        );

    }


}

export default MachineRecordTable;