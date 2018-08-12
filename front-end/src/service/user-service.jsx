import PGUtil    from 'util/util.jsx'
import PGConstant from 'util/constant.jsx'

const _util       = new PGUtil();

class User{
    farmerApply(farmerInfo){
        let url = PGConstant.base_url + '/my-machine/';
        return _util.request({
            type: 'post',
            url: url,
            data: farmerInfo
        });
    }

    login(loginInfo){
        let url = PGConstant.base_url + '/login/';
        return _util.request({
            type: 'post',
            url: url,
            data: loginInfo
        });
    }
    // check if the loginInfo is legel
    checkLoginInfo(loginInfo){
        let username = $.trim(loginInfo.username),
            password = $.trim(loginInfo.password);
        // check username
        if(typeof username !== 'string' || username.length ===0){
            return {
                status: false,
                msg: 'username cannot be an empty string!'
            }
        }
        // check password
        if(typeof password !== 'string' || password.length ===0){
            return {
                status: false,
                msg: 'password cannot be an empty string!！'
            }
        }
        return {
            status : true,
            msg : 'justify pass'
        }
    }
    // logout
    logout(){
        // let url = PGConstant.base_url + '/logout';
        // return _util.request({
        //     type    : 'post',
        //     url     : url
        // });
        return true;
    }

    getUserMachineManageList(listParam){
        let url = PGConstant.base_url + '/my-machine';
        return _util.request({
            type    : 'get',
            url     : url,
            data    : listParam
        //     listParam.page = page;
        //     listParam.username = this.state.username;
        });
    }

    getUserPortalInfo(username=''){
        let url = PGConstant.base_url + '/user-portal/' + username;
        return _util.request({
            type    : 'get',
            url     : url,
            data    : {}
        });
    }

}

export default User;