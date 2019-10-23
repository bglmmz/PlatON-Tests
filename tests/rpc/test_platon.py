import pytest
from client_sdk_python.eth import Eth
import allure

from eth_utils import (
    is_boolean,
    is_bytes,
    is_checksum_address,
    is_dict,
    is_integer,
    is_list_like,
    is_same_address,
    is_string,
)
from hexbytes import HexBytes
from client_sdk_python.exceptions import (
    InvalidAddress,
)

from common.log import log
import time

UNKNOWN_ADDRESS = '0xdEADBEeF00000000000000000000000000000000'
UNKNOWN_HASH = '0xdeadbeef00000000000000000000000000000000000000000000000000000000'
COMMON_ADDRESS = '0x55bfd49472fd41211545b01713a9c3a97af78b05'


@pytest.fixture(scope="module")
def unlocked_account(global_test_env):
    env = global_test_env
    node = env.get_rand_node()
    address = env.account.generate_account_in_node(node, '123456', 100000000000000000000000)
    env.account.unlock_account(node, address)
    return {
        'address': address,
        'node': node
    }

@pytest.fixture(scope="module")
def platon_connect(global_test_env):
    env = global_test_env
    node = env.get_rand_node()
    yield node.eth

@pytest.fixture(scope="module")
def block_with_txn(global_test_env):
    env = global_test_env
    node = env.get_rand_node()
    account = env.account.account_with_money
    res = env.account.sendTransaction(node.web3,'',account['address'],account['address'], node.eth.gasPrice, 21000, 10000)
    platon = Eth(node.web3)

    block = platon.getBlock(res['blockNumber'])
    log.info("blockNumber:::::::::{}".format(res['blockNumber']))
    log.info("blockInfo:::::::::{}".format(block))
    time.sleep(2)
    return block

@pytest.fixture(scope="module")
def empty_block(platon_connect):
    return platon_connect.getBlock(2)


# return block  with contract_address
@pytest.fixture(scope="module")
def block_with_txn_with_log(global_test_env):
    env = global_test_env
    node = env.get_rand_node()
    plan = [{"Epoch":1,"Amount":1000000}]

    log.info("send block_with_txn_with_log to host: {}".format(node.host))

    res = env.account.create_restricting_plan( node.web3,COMMON_ADDRESS,plan,env.account.account_with_money['address'],node.eth.gasPrice*2,30000000)
    platon = Eth(node.web3)

    block = platon.getBlock(res['blockNumber'])

    log.info("blockNumber:::::::::{}".format(res['blockNumber']))
    log.info("blockInfo:::::::::{}".format(block))
    time.sleep(2)

    return block



class TestPlaton():
    @pytest.mark.P1
    def test_getbalance(self, global_test_env,platon_connect):
        env = global_test_env
        account = env.account.get_rand_account()
        balance = platon_connect.getBalance(account['address'])
        assert balance >=0 , '账户余额相等'

    @allure.title("测试块高")
    @pytest.mark.P1
    def test_BlockNumber(self, platon_connect):
            """
            测试platon.getBlockNumber()
            """
            block_number = platon_connect.blockNumber
            assert is_integer(block_number)
            assert block_number >= 0

    @allure.title("测试协议版本")
    @pytest.mark.P1
    def test_ProtocolVersion(self,platon_connect):
        protocol_version = platon_connect.protocolVersion
        assert is_string(protocol_version)
        assert protocol_version.isdigit()

    @allure.title("查看同步状态")
    @pytest.mark.P1
    def test_syncing(self, platon_connect):
        syncing = platon_connect.syncing
        assert is_boolean(syncing) or is_dict(syncing)
        if is_boolean(syncing):
            assert syncing is False
        elif is_dict(syncing):
            assert 'startingBlock' in syncing
            assert 'currentBlock' in syncing
            assert 'highestBlock' in syncing

            assert is_integer(syncing['startingBlock'])
            assert is_integer(syncing['currentBlock'])
            assert is_integer(syncing['highestBlock'])

    @allure.title("查看gasPrice")
    @pytest.mark.P1
    def test_gasPrice(self, platon_connect):
        gas_price = platon_connect.gasPrice
        assert is_integer(gas_price)
        assert gas_price > 0

    @allure.title("查看节点账户数量")
    @pytest.mark.P1
    def test_accounts(self, global_test_env):
        env = global_test_env
        node = env.get_rand_node()

        platon = Eth(node.web3)

        accounts_before = platon.accounts
        i = 0
        while i<10:
            env.account.generate_account_in_node(node, '123456')
            i+=1
        accounts_after = platon.accounts

        assert is_list_like(accounts_after)
        assert len(accounts_after) == len(accounts_before)+10
        assert all((
            is_checksum_address(account)
            for account
            in accounts_after
        ))

    @allure.title("查看Storage")
    @pytest.mark.P1
    def test_getStorageAt(self, global_test_env):
        env = global_test_env
        node = env.get_rand_node()
        account = env.account.get_rand_account()
        platon = Eth(node.web3)

        storage = platon.getStorageAt(account['address'], 0)
        assert isinstance(storage, HexBytes)

    @allure.title("使用不存在的地址查看Storage")
    @pytest.mark.P1
    def test_getStorageAt_invalid_address(self, platon_connect):
        with pytest.raises(InvalidAddress):
            platon_connect.getStorageAt(UNKNOWN_ADDRESS.lower(), 0)

    @allure.title("查看交易数量")
    @pytest.mark.P1
    def test_getTransactionCount(self, global_test_env):
        env = global_test_env
        node = env.get_rand_node()
        platon = Eth(node.web3)
        transaction_count = platon.getTransactionCount(env.account.get_rand_account()['address'])
        assert is_integer(transaction_count)
        assert transaction_count >= 0

    @allure.title("使用不存在的账号查看交易数量")
    @pytest.mark.P1
    def test_getTransactionCount_invalid_address(self, platon_connect):
        with pytest.raises(InvalidAddress):
            platon_connect.getTransactionCount(UNKNOWN_ADDRESS.lower())

    @allure.title("通过空块的hash查看的交易数量")
    @pytest.mark.P1
    def test_getBlockTransactionCountByHash_empty_block(self, platon_connect,empty_block):
        transaction_count = platon_connect.getBlockTransactionCount(empty_block['hash'])
        assert is_integer(transaction_count)
        assert transaction_count == 0

    @allure.title("通过空块的块高查看交易数量")
    @pytest.mark.P1
    def test_platon_getBlockTransactionCountByNumber_empty_block(self, platon_connect,empty_block):
        transaction_count = platon_connect.getBlockTransactionCount(empty_block['number'])
        assert is_integer(transaction_count)
        assert transaction_count == 0

    @pytest.mark.P1
    def test_platon_getBlockTransactionCountByHash_block_with_txn(self, platon_connect, block_with_txn):
        transaction_count = platon_connect.getBlockTransactionCount(block_with_txn['hash'])
        assert is_integer(transaction_count)
        assert transaction_count >= 1

    @pytest.mark.P1
    def test_platon_getBlockTransactionCountByNumber_block_with_txn(self, platon_connect,block_with_txn):
        transaction_count = platon_connect.getBlockTransactionCount(block_with_txn['number'])
        assert is_integer(transaction_count)
        assert transaction_count >= 1

    # def test_eth_getCode(self, global_test_env):
    #     #todo 怎么创建合约
    #     env = global_test_env
    #     node = env.get_rand_node()
    #     platon = Eth(node.connect_node())
    #
    #     account = env.aacount.get_rand_account()
    #
    #     code = platon.getCode(account)
    #     assert isinstance(code, HexBytes)
    #     assert len(code) > 0
    #
    # def test_eth_getCode_invalid_address(self, global_test_env):
    #     env = global_test_env
    #     node = env.get_rand_node()
    #     platon = Eth(node.connect_node())
    #     with pytest.raises(InvalidAddress):
    #         platon.getCode(UNKNOWN_ADDRESS)

    # def test_eth_getCode_with_block_identifier(self, global_test_env):
    #     #code = web3.eth.getCode(emitter_contract.address, block_identifier=web3.eth.blockNumber)
    #     assert isinstance(code, HexBytes)
    #     assert len(code) > 0
    #

    @pytest.mark.P1
    def test_platon_sign(self, unlocked_account):

        platon = Eth(unlocked_account['node'].web3)

        signature = platon.sign(
            unlocked_account['address'], text='Message tö sign. Longer than hash!'
        )
        assert is_bytes(signature)
        assert len(signature) == 32 + 32 + 1

        # test other formats
        hexsign = platon.sign(
            unlocked_account['address'],
            hexstr='0x4d6573736167652074c3b6207369676e2e204c6f6e676572207468616e206861736821'
        )
        assert hexsign == signature

        intsign = platon.sign(
            unlocked_account['address'],
            0x4d6573736167652074c3b6207369676e2e204c6f6e676572207468616e206861736821
        )
        assert intsign == signature

        bytessign = platon.sign(
            unlocked_account['address'], b'Message t\xc3\xb6 sign. Longer than hash!'
        )
        assert bytessign == signature

        new_signature =platon.sign(
            unlocked_account['address'], text='different message is different'
        )
        assert new_signature != signature

    @pytest.mark.P1
    def test_platon_sendTransaction_addr_checksum_required(self, unlocked_account):

        platon = Eth(unlocked_account['node'].web3)

        address = unlocked_account['address'].lower()
        txn_params = {
            'from': address,
            'to': address,
            'value': 1,
            'gas': 21000,
            'gasPrice': platon.gasPrice,
        }
        with pytest.raises(InvalidAddress):
            invalid_params = dict(txn_params, **{'from':UNKNOWN_ADDRESS})
            platon.sendTransaction(invalid_params)

        with pytest.raises(InvalidAddress):
            invalid_params = dict(txn_params, **{'to': UNKNOWN_ADDRESS})
            platon.sendTransaction(invalid_params)

    @pytest.mark.P1
    def test_platon_sendTransaction(self, unlocked_account):

        platon = Eth(unlocked_account['node'].web3)

        txn_params = {
            'from': unlocked_account['address'],
            'to': unlocked_account['address'],
            'value': 1,
            'gas': 21000,
            'gasPrice': platon.gasPrice,
        }
        txn_hash = platon.sendTransaction(txn_params)
        txn = platon.getTransaction(txn_hash)

        assert is_same_address(txn['from'], txn_params['from'])
        assert is_same_address(txn['to'], txn_params['to'])
        assert txn['value'] == 1
        assert txn['gas'] == 21000
        assert txn['gasPrice'] == txn_params['gasPrice']


    @pytest.mark.P1
    def test_platon_sendTransaction_with_nonce(self, unlocked_account):

        platon = Eth(unlocked_account['node'].web3)
        txn_params = {
            'from': unlocked_account['address'],
            'to': unlocked_account['address'],
            'value': 1,
            'gas': 21000,
            # Increased gas price to ensure transaction hash different from other tests
            'gasPrice': platon.gasPrice * 2,
            'nonce': platon.getTransactionCount(unlocked_account['address']),
        }
        txn_hash = platon.sendTransaction(txn_params)
        txn = platon.getTransaction(txn_hash)

        assert is_same_address(txn['from'], txn_params['from'])
        assert is_same_address(txn['to'], txn_params['to'])
        assert txn['value'] == 1
        assert txn['gas'] == 21000
        assert txn['gasPrice'] == txn_params['gasPrice']
       # assert txn['nonce'] == txn_params['nonce']

    @pytest.mark.P1
    def test_platon_replaceTransaction(self, unlocked_account):
        platon = Eth(unlocked_account['node'].web3)
        txn_params = {
            'from': unlocked_account['address'],
            'to': unlocked_account['address'],
            'value': 3,
            'gas': 21000,
            'gasPrice': platon.gasPrice,
            'nonce': 1000,
        }
        txn_hash = platon.sendTransaction(txn_params)
        txn_params['gasPrice'] = platon.gasPrice * 2
        replace_txn_hash = platon.replaceTransaction(txn_hash, txn_params)
        replace_txn = platon.getTransaction(replace_txn_hash)

        assert is_same_address(replace_txn['from'], txn_params['from'])
        assert is_same_address(replace_txn['to'], txn_params['to'])
        assert replace_txn['value'] == 3
        assert replace_txn['gas'] == 21000
        assert replace_txn['gasPrice'] == txn_params['gasPrice']

    @pytest.mark.P1
    def test_platon_replaceTransaction_non_existing_transaction(self, unlocked_account):
        platon = Eth(unlocked_account['node'].web3)

        txn_params = {
            'from': unlocked_account['address'],
            'to': unlocked_account['address'],
            'value': 1,
            'gas': 21000,
            'gasPrice': platon.gasPrice,
        }
        with pytest.raises(ValueError):
            platon.replaceTransaction(
                '0x98e8cc09b311583c5079fa600f6c2a3bea8611af168c52e4b60b5b243a441997',
                txn_params
            )

    # auto mine is enabled for this test
    @pytest.mark.P1
    def test_platon_replaceTransaction_already_mined(self, unlocked_account):

        platon = Eth(unlocked_account['node'].web3)
        address = unlocked_account['address']

        txn_params = {
            'from': address,
            'to': address,
            'value': 76,
            'gas': 21000,
            'gasPrice': platon.gasPrice*4,
        }
        txn_hash = platon.sendTransaction(txn_params)
        txn_params['gasPrice'] = platon.gasPrice * 5
        platon.waitForTransactionReceipt(txn_hash)
        with pytest.raises(ValueError):
            platon.replaceTransaction(txn_hash, txn_params)

    @pytest.mark.P1
    def test_platon_replaceTransaction_incorrect_nonce(self, unlocked_account):
        platon = Eth(unlocked_account['node'].web3)
        address = unlocked_account['address']
        txn_params = {
            'from': address,
            'to': address,
            'value': 1,
            'gas': 21000,
            'gasPrice': platon.gasPrice,
        }
        txn_hash =platon.sendTransaction(txn_params)
        txn = platon.getTransaction(txn_hash)

        txn_params['gasPrice'] =platon.gasPrice * 2
        txn_params['nonce'] = int(txn['nonce'],16) + 1
        with pytest.raises(ValueError):
            platon.replaceTransaction(txn_hash, txn_params)

    @pytest.mark.P1
    def test_platon_replaceTransaction_gas_price_too_low(self, unlocked_account):
        platon = Eth(unlocked_account['node'].web3)
        address = unlocked_account['address']
        txn_params = {
            'from': address,
            'to': address,
            'value': 1,
            'gas': 21000,
            'gasPrice': platon.gasPrice,
        }
        txn_hash = platon.sendTransaction(txn_params)

        txn_params['gasPrice'] = 9
        with pytest.raises(ValueError):
            platon.replaceTransaction(txn_hash, txn_params)

    @pytest.mark.P1
    def test_platon_replaceTransaction_gas_price_defaulting_minimum(self, unlocked_account):
        platon = Eth(unlocked_account['node'].web3)
        address = unlocked_account['address']
        txn_params = {
            'from': address,
            'to': address,
            'value': 1,
            'gas': 21000,
            'gasPrice': platon.gasPrice,
        }
        txn_hash = platon.sendTransaction(txn_params)

        txn_params.pop('gasPrice')
        replace_txn_hash = platon.replaceTransaction(txn_hash, txn_params)
        replace_txn = platon.getTransaction(replace_txn_hash)

        # todo minimum gas price is what
        assert replace_txn['gasPrice'] == int( platon.gasPrice*1.1)

    @pytest.mark.P1
    def test_platon_replaceTransaction_gas_price_defaulting_strategy_higher(self,unlocked_account):
        node = unlocked_account['node']
        platon = Eth(node.web3)
        price = platon.gasPrice

        txn_params = {
            'from': unlocked_account['address'],
            'to': UNKNOWN_ADDRESS,
            'value': 1,
            'gas': 21000,
            'gasPrice': price*10,
            'nonce': 1000,
        }

        txn_hash = platon.sendTransaction(txn_params)

        def higher_gas_price_strategy(web3, txn):
            return price*20

        platon.setGasPriceStrategy(higher_gas_price_strategy)
        node.web3.eth = platon


        txn_params.pop('gasPrice')

        replace_txn_hash = platon.replaceTransaction(txn_hash, txn_params)
        replace_txn = platon.getTransaction(replace_txn_hash)
        log.info(replace_txn)
        assert replace_txn['gasPrice'] == price*20 # Strategy provides higher gas price

    @pytest.mark.P1
    def test_platon_replaceTransaction_gas_price_defaulting_strategy_lower(self, unlocked_account):

        node = unlocked_account['node']
        platon = Eth(node.web3)
        price = platon.gasPrice
        txn_params = {
            'from': unlocked_account['address'],
            'to': unlocked_account['address'],
            'value': 3,
            'gas': 21000,
            'gasPrice': price * 2,
            'nonce': 3000,
        }

        txn_hash = platon.sendTransaction(txn_params)

        def lower_gas_price_strategy(web3, txn):
            return price

        platon.setGasPriceStrategy(lower_gas_price_strategy)

        node.web3.eth = platon

        txn_params.pop('gasPrice')
        replace_txn_hash = platon.replaceTransaction(txn_hash, txn_params)

        replace_txn = platon.getTransaction(replace_txn_hash)

        # Strategy provices lower gas price - minimum preferred
        assert replace_txn['gasPrice'] == int(price * 2*1.1)

    #todo  需要一个出块很慢的环境
    # def test_platon_modifyTransaction(self,  unlocked_account):
    #     node = unlocked_account['node']
    #     platon = Eth(node.web3)
    #     txn_params = {
    #         'from': unlocked_account['address'],
    #         'to': unlocked_account['address'],
    #         'value': 1,
    #         'gas': 21000,
    #         'gasPrice': platon.gasPrice,
    #         'nonce': platon.getTransactionCount(unlocked_account['address'])
    #     }
    #     txn_hash = platon.sendTransaction(txn_params)
    #
    #     modified_txn_hash =platon.modifyTransaction(
    #         txn_hash, gasPrice=(txn_params['gasPrice'] * 2), value=2
    #     )
    #     modified_txn = platon.getTransaction(modified_txn_hash)
    #
    #     assert is_same_address(modified_txn['from'], txn_params['from'])
    #     assert is_same_address(modified_txn['to'], txn_params['to'])
    #     assert modified_txn['value'] == 2
    #     assert modified_txn['gas'] == 21000
    #     assert modified_txn['gasPrice'] == txn_params['gasPrice'] * 2

    @pytest.mark.P1
    def test_platon_sendRawTransaction(self,global_test_env):
        env = global_test_env
        node = env.get_rand_node()
        account = env.account.account_with_money
        platon = Eth(node.web3)

        transaction_dict = {
            "to": account['address'],
            "gasPrice": platon.gasPrice,
            "gas": 21000,
            "nonce": account['nonce'],
            "data": '',
            "chainId": global_test_env.account.chain_id,
            "value": '0x10'
        }
        signedTransactionDict = platon.account.signTransaction(
            transaction_dict, account['prikey']
        )

        data = signedTransactionDict.rawTransaction


        txn_hash = platon.sendRawTransaction(data)
        platon.waitForTransactionReceipt(txn_hash)
        assert txn_hash == signedTransactionDict.hash

    # todo 合约调用
    # def test_platon_call(self, web3, math_contract):
    #     coinbase = web3.eth.coinbase
    #     txn_params = math_contract._prepare_transaction(
    #         fn_name='add',
    #         fn_args=(7, 11),
    #         transaction={'from': coinbase, 'to': math_contract.address},
    #     )
    #     call_result = web3.eth.call(txn_params)
    #     assert is_string(call_result)
    #     result = decode_single('uint256', call_result)
    #     assert result == 18

    # def test_eth_call_with_0_result(self, web3, math_contract):
    #     coinbase = web3.eth.coinbase
    #     txn_params = math_contract._prepare_transaction(
    #         fn_name='add',
    #         fn_args=(0, 0),
    #         transaction={'from': coinbase, 'to': math_contract.address},
    #     )
    #     call_result = web3.eth.call(txn_params)
    #     assert is_string(call_result)
    #     result = decode_single('uint256', call_result)
    #     assert result == 0

    @pytest.mark.P1
    def test_platon_estimateGas(self, unlocked_account):
        node = unlocked_account['node']
        platon = Eth(node.web3)

        gas_estimate = platon.estimateGas({
            'from': unlocked_account['address'],
            'to': unlocked_account['address'],
            'value': 1,
        })
        assert is_integer(gas_estimate)
        assert gas_estimate > 0

    @pytest.mark.P1
    def test_platon_getBlockByHash(self, platon_connect):
        empty_block = platon_connect.getBlock(1)

        block = platon_connect.getBlock(empty_block['hash'])
        assert block['hash'] == empty_block['hash']

    @pytest.mark.P1
    def test_platon_getBlockByHash_not_found(self, platon_connect):
        block =platon_connect.getBlock(UNKNOWN_HASH)
        assert block is None

    @pytest.mark.P1
    def test_platon_getBlockByNumber_with_integer(self, platon_connect):
        block = platon_connect.getBlock(1)
        assert block['number'] == 1

    @pytest.mark.P1
    def test_platon_getBlockByNumber_latest(self, platon_connect):
        block = platon_connect.getBlock('latest')
        assert block['number'] > 0

    @pytest.mark.P1
    def test_platon_getBlockByNumber_not_found(self, platon_connect):
        block = platon_connect.getBlock(123456789)
        assert block is None

    @pytest.mark.P1
    def test_platon_getBlockByNumber_pending(self, platon_connect):
        block = platon_connect.getBlock('pending')
        latest = platon_connect.getBlock('latest')

        assert block['number'] == latest['number'] + 2

    @pytest.mark.P1
    def test_platon_getBlockByNumber_earliest(self, platon_connect):
        genesis_block = platon_connect.getBlock(0)
        block = platon_connect.getBlock('earliest')
        assert block['number'] == 0
        assert block['hash'] == genesis_block['hash']

    @pytest.mark.P1
    def test_platon_getBlockByNumber_full_transactions(self, platon_connect,block_with_txn):
        block = platon_connect.getBlock(block_with_txn['number'], True)
        transaction = block['transactions'][0]
        assert transaction['hash'] == block_with_txn['transactions'][0]

    @pytest.mark.P1
    def test_platon_getTransactionByHash(self, block_with_txn,platon_connect):

        transaction = platon_connect.getTransaction(block_with_txn['transactions'][0])
        assert is_dict(transaction)
        assert transaction['hash'] == block_with_txn['transactions'][0]

    # def test_platon_getTransactionByHash_contract_creation(self,
    #                                                     web3,
    #                                                     math_contract_deploy_txn_hash):
    #     transaction = web3.eth.getTransaction(math_contract_deploy_txn_hash)
    #     assert is_dict(transaction)
    #     assert transaction['to'] is None, "to field is %r" % transaction['to']

    @pytest.mark.P1
    def test_platon_getTransactionFromBlockHashAndIndex(self, platon_connect,block_with_txn):


        transaction =platon_connect.getTransactionFromBlock(block_with_txn['hash'], 0)
        assert is_dict(transaction)
        assert transaction['hash'] == HexBytes(block_with_txn['transactions'][0])

    @pytest.mark.P1
    def test_platon_getTransactionFromBlockNumberAndIndex(self,platon_connect,block_with_txn):
        transaction = platon_connect.getTransactionFromBlock(block_with_txn['number'], 0)
        assert is_dict(transaction)
        assert transaction['hash'] == HexBytes(block_with_txn['transactions'][0])

    @pytest.mark.P1
    def test_platon_getTransactionReceipt_mined(self, platon_connect, block_with_txn):
        receipt = platon_connect.getTransactionReceipt(block_with_txn['transactions'][0])
        assert is_dict(receipt)
        assert receipt['blockNumber'] == block_with_txn['number']
        assert receipt['blockHash'] == block_with_txn['hash']
        assert receipt['transactionIndex'] == 0
        assert receipt['transactionHash'] == HexBytes(block_with_txn['transactions'][0])

    @pytest.mark.P1
    def test_platon_getTransactionReceipt_unmined(self, unlocked_account):

        platon = Eth(unlocked_account['node'].web3)

        txn_hash = platon.sendTransaction({
            'from': unlocked_account['address'],
            'to': unlocked_account['address'],
            'value': 1,
            'gas': 21000,
            'gasPrice': platon.gasPrice,
        })
        receipt = platon.getTransactionReceipt(txn_hash)
        assert receipt is None

    @pytest.mark.P1
    def test_platon_getTransactionReceipt_with_log_entry(self, platon_connect, block_with_txn_with_log):

        log.info("block in test_platon_getTransactionReceipt_with_log_entry:::{}".format(block_with_txn_with_log))
        receipt = platon_connect.getTransactionReceipt(block_with_txn_with_log['transactions'][0])
        log.info(" tx:{}, receipt:::{}".format(block_with_txn_with_log['transactions'][0].hex(),receipt))

        assert is_dict(receipt)
        assert receipt['blockNumber'] == block_with_txn_with_log['number']
        assert receipt['blockHash'] == block_with_txn_with_log['hash']
        assert receipt['transactionIndex'] == 0
       # assert receipt['transactionHash'] == HexBytes(block_with_txn_with_log['receiptsRoot'])

        assert len(receipt['logs']) == 1
        log_entry = receipt['logs'][0]

        assert log_entry['blockNumber'] == block_with_txn_with_log['number']
        assert log_entry['blockHash'] == block_with_txn_with_log['hash']
        assert log_entry['logIndex'] == 0
        # assert is_same_address(log_entry['address'],  block_with_txn_with_log['contract_address'])
        assert log_entry['transactionIndex'] == 0
        # assert log_entry['transactionHash'] == HexBytes(block_with_txn_with_log['transactionsRoot'])









